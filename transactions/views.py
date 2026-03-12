from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TransactionForm
from .models import Transaction


@login_required
def transaction_list(request):
	"""Display all transactions that belong to the current user."""
	transactions = Transaction.objects.filter(user=request.user)
	return render(
		request,
		"transactions/list.html",
		{
			"transactions": transactions,
			"page_title": "My Transactions",
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
