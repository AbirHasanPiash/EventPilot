from django.urls import path
from .views import ActivateUserView


urlpatterns = [
    path('activate/<uidb64>/<token>/', ActivateUserView.as_view(), name='activate-user'),
]
