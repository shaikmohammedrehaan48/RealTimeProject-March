from django.urls import path

from .views import dashboard

app_name = 'expenses'

urlpatterns = [
    path('', dashboard, name='dashboard'),
]
