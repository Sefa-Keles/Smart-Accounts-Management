from django.urls import path

from . import views

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("create/", views.transaction_create, name="transaction_create"),
    path("export/csv/", views.transaction_export_csv, name="transaction_export_csv"),
    path("export/pdf/", views.transaction_export_pdf, name="transaction_export_pdf"),
    path("<int:transaction_id>/edit/", views.transaction_edit, name="transaction_edit"),
    path("<int:transaction_id>/delete/", views.transaction_delete, name="transaction_delete"),
]
