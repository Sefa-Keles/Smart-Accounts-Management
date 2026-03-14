from django.urls import path

from .views import (
    category_delete,
    category_list,
    create_checkout_session,
    dashboard,
    home,
    subscription_cancel,
    subscription_plans,
    subscription_success,
)

urlpatterns = [
    path('', home, name='home'),
    path('dashboard/', dashboard, name='dashboard'),
    path('categories/', category_list, name='category_list'),
    path('categories/<int:category_id>/delete/', category_delete, name='category_delete'),
    path('subscription/plans/', subscription_plans, name='subscription_plans'),
    path('subscription/checkout/', create_checkout_session, name='create_checkout_session'),
    path('subscription/success/', subscription_success, name='subscription_success'),
    path('subscription/cancel/', subscription_cancel, name='subscription_cancel'),
]
