from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/defects/', include("defects.urls")),
    path('api/auth/', include('authentication.urls')),

# Раздача HTML страниц
    path('login/', TemplateView.as_view(template_name='authentication/login.html')),
    path('defects/', TemplateView.as_view(template_name='defects/defects_table.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
