from django.urls import path

from . import views

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("export/csv/", views.transaction_export_csv, name="transaction_export_csv"),
    path("<int:transaction_id>/edit/", views.transaction_edit, name="transaction_edit"),
    path("<int:transaction_id>/delete/", views.transaction_delete, name="transaction_delete"),
]
