import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .services.fingerprint import generate_device_fingerprint, get_client_ip
from .serializers import RegisterSerializer, LoginSerializer, LogoutSerializer
from .services.redis_service import redis_token_service

logger = logging.getLogger(__name__)

class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,

                }
            },status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    User login endpoint - issues JWT tokens and ads to whitelist
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        logger.info(f"Logout data {request.data}")
        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Generate fingerprint
            device_fingerprint = generate_device_fingerprint(request)
            ip_address = get_client_ip(request)
            user_agent = request.headers.get('User-Agent', '')

            # Generate token
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            # Prepare metadata
            token_metadata = {
                'token_type': 'access',
                'device_fingerprint': device_fingerprint,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'login_time': datetime.now().isoformat(),
            }

            # Add tokens to whitelist with metadata
            refresh_jti = refresh['jti']
            refresh_exp = datetime.fromtimestamp(refresh['exp'])
            redis_token_service.add_to_whitelist(
                refresh_jti,
                user.id,
                refresh_exp,
                {'token_type': 'refresh', **token_metadata}
            )

            # Add access token to whitelist
            access_jti = access_token['jti']
            access_exp = datetime.fromtimestamp(access_token['exp'])

            redis_token_service.add_to_whitelist(
                access_jti,
                user.id,
                access_exp,
                token_metadata,
            )

            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """
    User logout endpoint
    """
    permission_classes = [IsAuthenticated]

    @csrf_exempt
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)

        if serializer.is_valid():
            try:
                refresh_token = serializer.validated_data['refresh']
                token = RefreshToken(refresh_token)

                # Remove from whitelist
                refresh_jti = token['jti']
                refresh_exp = datetime.fromtimestamp(token['exp'])
                redis_token_service.remove_from_whitelist(refresh_jti)

                # Add access token to blacklist if provided in header
                # Access token JTI is extracted from request
                if hasattr(request, 'auth') and request.auth:
                    access_jti = request.auth.get('jti')
                    if access_jti:
                        access_exp = datetime.fromtimestamp(request.auth.get('exp'))
                        redis_token_service.add_to_blacklist(access_jti, request.user.id, access_exp)
                        redis_token_service.remove_from_whitelist(access_jti)
                return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f'Logout error {e}')
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAllView(APIView):
    """
    Logout from all devices - revoke all user tokens
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        success = redis_token_service.revoke_all_tokens(request.user_id)

        if success:
            return Response({
                'message': 'Successfully logged out from all devices'
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Failed to revoke tokens'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenRefreshView(APIView):
    """
    Refresh access token using refresh token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)

            # Check if refresh token is blacklisted
            if redis_token_service.is_blacklisted():
                return Response({'error': 'Refresh token is blacklisted'}, status=status.HTTP_401_UNAUTHORIZED)

            # Check if whitelisted

            if settings.WHITELIST_ENABLED and not redis_token_service.is_whitelisted(refresh['jti']):
                return Response({'error': 'Token not authorized'}, status=status.HTTP_401_UNAUTHORIZED)


            # Create new access token
            new_access_token = refresh.access_token

            # Add new access token to whitelist
            user_id = refresh['user_id']
            access_exp = datetime.fromtimestamp(new_access_token['exp'])
            redis_token_service.add_to_whitelist(
                new_access_token['jti'],
                user_id,
                access_exp,
                {'token_type': 'access'}
            )

            return Response({
                'access': str(new_access_token)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return Response({'error': 'Invalid refresh token'}, status=status.HTTP_401_UNAUTHORIZED)


class TokenVerifyView(APIView):
    """
    Verify if token is valid
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):

        token_data = {
            'user_id': request.user.id,
            'username': request.user.username,
            'token_valid': True,
            'token_jti': request.auth.get('jti') if request.auth else None
        }

        return Response(token_data, status=status.HTTP_200_OK)
