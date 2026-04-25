from django.urls import path

from .views import (
    RegisterView, LoginView, LogoutView, LogoutAllView,
    TokenRefreshView, TokenVerifyView
)

app_name = "authentication"

urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/logout-all/', LogoutAllView.as_view(), name='logout-all'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

]