from django.urls import path
from . import views  # Import your views file

urlpatterns = [
    path('batch/<int:batch_id>/', views.view_batch, name='view_batch'),
]