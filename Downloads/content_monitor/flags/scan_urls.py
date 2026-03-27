from django.urls import path
from .scan_view import ScanView

urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
]