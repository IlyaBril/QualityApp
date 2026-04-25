from django.urls import path
from .views import DefectsListView
from rest_framework.routers import DefaultRouter

# router = DefaultRouter()
# router.register(r'table', DefectsListView, basename='defects_table')
# urlpatterns = router.urls

urlpatterns = [
    path("table/", DefectsListView.as_view(), name="defects_table"),
]
