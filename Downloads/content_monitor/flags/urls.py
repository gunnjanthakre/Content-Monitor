from django.urls import path
from .views import FlagListView, FlagDetailView

urlpatterns = [
    path('', FlagListView.as_view(), name='flag-list'),
    path('<int:pk>/', FlagDetailView.as_view(), name='flag-detail'),
]