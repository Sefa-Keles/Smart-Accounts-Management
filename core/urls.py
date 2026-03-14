from django.urls import path

from .views import category_delete, category_list, dashboard, home

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('categories/', category_list, name='category_list'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),
]
