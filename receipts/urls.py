from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_receipt, name='upload_receipt'),
    path('', views.receipt_list, name='receipt_list'),
    path('<int:receipt_id>/', views.receipt_detail, name='receipt_detail'),
]
