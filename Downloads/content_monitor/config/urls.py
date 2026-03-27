from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('keywords/', include('keywords.urls')),
    path('scan/', include('flags.scan_urls')),
    path('flags/', include('flags.urls')),
]