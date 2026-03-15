import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from core.plan_limits import can_create_transaction, get_monthly_usage

from .forms import TransactionForm
from .models import Transaction


def _get_filtered_transactions(request, persist_filters=True):
	"""Return user transactions filtered by month or date range."""
	today = timezone.now().date()
	session_filters = request.session.get("transaction_filters", {})

	clear_filters = request.GET.get("clear_filters") == "1"
	request_has_filter_params = any(
		key in request.GET for key in ["month", "start_date", "end_date"]
	)

	if clear_filters:
		request.session.pop("transaction_filters", None)
		selected_month = today.strftime("%Y-%m")
		start_date = ""
		end_date = ""
	elif request_has_filter_params:
		selected_month = request.GET.get("month", "").strip()
		start_date = request.GET.get("start_date", "").strip()
		end_date = request.GET.get("end_date", "").strip()
		if persist_filters:
			request.session["transaction_filters"] = {
				"month": selected_month,
				"start_date": start_date,
				"end_date": end_date,
			}
	else:
		selected_month = session_filters.get("month", today.strftime("%Y-%m"))
		start_date = session_filters.get("start_date", "")
		end_date = session_filters.get("end_date", "")

	transactions = Transaction.objects.filter(user=request.user)
	filter_label = "Current month"

	if start_date and end_date:
		try:
			start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
			end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
			transactions = transactions.filter(date__range=[start_obj, end_obj])
			filter_label = f"{start_obj:%d %b %Y} - {end_obj:%d %b %Y}"
		except ValueError:
			selected_month = today.strftime("%Y-%m")
			start_date = ""
			end_date = ""

	if not start_date or not end_date:
		if selected_month:
			try:
				year, month = selected_month.split("-")
				transactions = transactions.filter(date__year=int(year), date__month=int(month))
				filter_label = datetime(int(year), int(month), 1).strftime("%B %Y")
			except (ValueError, TypeError):
				transactions = transactions.filter(date__year=today.year, date__month=today.month)
				selected_month = today.strftime("%Y-%m")
		else:
			transactions = transactions.filter(date__year=today.year, date__month=today.month)
			selected_month = today.strftime("%Y-%m")

	transactions = transactions.order_by("-date", "-created_at")
	return transactions, selected_month, start_date, end_date, filter_label


@login_required
def transaction_list(request):
	"""Display all transactions that belong to the current user."""
	transactions, selected_month, start_date, end_date, filter_label = _get_filtered_transactions(
		request,
		persist_filters=True,
	)
	return render(
		request,
		"transactions/list.html",
		{
			"transactions": transactions,
			"page_title": "My Transactions",
			"selected_month": selected_month,
			"start_date": start_date,
			"end_date": end_date,
			"filter_label": filter_label,
		},
	)


@login_required
def transaction_export_csv(request):
	"""Export all or filtered transactions as CSV."""
	scope = request.GET.get("scope", "filtered")

	if scope == "all":
		transactions = Transaction.objects.filter(user=request.user).order_by("-date", "-created_at")
	else:
		transactions, _, _, _, _ = _get_filtered_transactions(request, persist_filters=False)

	response = HttpResponse(content_type="text/csv")
	response["Content-Disposition"] = (
		f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
	)

	writer = csv.writer(response)
	writer.writerow(["date", "vendor", "description", "category", "amount", "type", "business_personal_flag"])

	for tx in transactions.select_related("category"):
		category_name = tx.category.name if tx.category else ""
		writer.writerow(
			[
				tx.date.isoformat(),
				tx.vendor_name,
				tx.description or "",
				category_name,
				str(tx.amount),
				tx.transaction_type,
				tx.flag,
			]
		)

	return response


@login_required
def transaction_export_pdf(request):
	"""Export all or filtered transactions as PDF."""
	scope = request.GET.get("scope", "filtered")

	if scope == "all":
		transactions = Transaction.objects.filter(user=request.user).order_by("-date", "-created_at")
		report_title = "All Transactions"
	else:
		transactions, _, _, _, filter_label = _get_filtered_transactions(request, persist_filters=False)
		report_title = f"Filtered Transactions ({filter_label})"

	response = HttpResponse(content_type="application/pdf")
	response["Content-Disposition"] = (
		f'attachment; filename="transactions_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
	)

	pdf = canvas.Canvas(response, pagesize=letter)
	page_width, page_height = letter
	y = page_height - 50

	pdf.setFont("Helvetica-Bold", 14)
	pdf.drawString(40, y, "Smart Accounts - Transactions Report")
	y -= 20
	pdf.setFont("Helvetica", 10)
	pdf.drawString(40, y, report_title)
	y -= 15
	pdf.drawString(40, y, f"Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
	y -= 25

	pdf.setFont("Helvetica-Bold", 10)
	pdf.drawString(40, y, "Date")
	pdf.drawString(95, y, "Vendor")
	pdf.drawString(200, y, "Description")
	pdf.drawString(320, y, "Category")
	pdf.drawString(395, y, "Type")
	pdf.drawString(445, y, "Flag")
	pdf.drawString(500, y, "Amount")
	y -= 12
	pdf.line(40, y, page_width - 40, y)
	y -= 15

	pdf.setFont("Helvetica", 9)
	for tx in transactions.select_related("category"):
		if y < 50:
			pdf.showPage()
			y = page_height - 50
			pdf.setFont("Helvetica-Bold", 10)
			pdf.drawString(40, y, "Date")
			pdf.drawString(95, y, "Vendor")
			pdf.drawString(200, y, "Description")
			pdf.drawString(320, y, "Category")
			pdf.drawString(395, y, "Type")
			pdf.drawString(445, y, "Flag")
			pdf.drawString(500, y, "Amount")
			y -= 12
			pdf.line(40, y, page_width - 40, y)
			y -= 15
			pdf.setFont("Helvetica", 9)

		vendor_text = (tx.vendor_name or "")[:18]
		description_text = (tx.description or "-")[:24]
		category_text = (tx.category.name if tx.category else "-")[:11]
		amount_text = str(tx.amount)

		pdf.drawString(40, y, tx.date.isoformat())
		pdf.drawString(95, y, vendor_text)
		pdf.drawString(200, y, description_text)
		pdf.drawString(320, y, category_text)
		pdf.drawString(395, y, tx.transaction_type.title())
		pdf.drawString(445, y, tx.flag.title())
		pdf.drawRightString(page_width - 40, y, amount_text)
		y -= 15

	pdf.save()
	return response


@login_required
def transaction_create(request):
	"""Create a manual transaction for the current user."""
	allowed, plan, limit_value = can_create_transaction(request.user)
	monthly_usage = get_monthly_usage(request.user)

	if request.method == "POST":
		if not allowed:
			messages.error(
				request,
				f"{plan.title()} plan monthly transaction limit reached ({limit_value}). Upgrade your subscription to continue.",
			)
			return redirect("subscription_plans")

		form = TransactionForm(request.POST, user=request.user)
		if form.is_valid():
			transaction = form.save(commit=False)
			transaction.user = request.user
			transaction.save()
			messages.success(request, "Transaction created successfully.")
			return redirect("transaction_list")
	else:
		form = TransactionForm(user=request.user)

	return render(
		request,
		"transactions/create.html",
		{
			"form": form,
			"transaction_limit_reached": not allowed,
			"current_plan": plan,
			"transaction_limit_value": limit_value,
			"transaction_usage": monthly_usage.get("transactions", 0),
			"page_title": "Add Transaction",
		},
	)


@login_required
def transaction_edit(request, transaction_id):
	"""Edit a single transaction owned by the current user."""
	transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

	if request.method == "POST":
		form = TransactionForm(request.POST, instance=transaction, user=request.user)
		if form.is_valid():
			form.save()
			messages.success(request, "Transaction updated successfully.")
			return redirect("transaction_list")
	else:
		form = TransactionForm(instance=transaction, user=request.user)

	return render(
		request,
		"transactions/edit.html",
		{
			"transaction": transaction,
			"form": form,
			"page_title": "Edit Transaction",
		},
	)


@login_required
def transaction_delete(request, transaction_id):
	"""Delete a transaction owned by the current user after confirmation."""
	transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

	if request.method == "POST":
		transaction.delete()
		messages.success(request, "Transaction deleted successfully.")
		return redirect("transaction_list")

	return render(
		request,
		"transactions/delete.html",
		{
			"transaction": transaction,
			"page_title": "Delete Transaction",
		},
	)
