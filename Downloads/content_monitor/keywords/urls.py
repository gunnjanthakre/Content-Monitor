from django.urls import path
from .views import KeywordListCreateView

urlpatterns = [
    path('', KeywordListCreateView.as_view(), name='keyword-list-create'),
]