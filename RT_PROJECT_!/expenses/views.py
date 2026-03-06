from decimal import Decimal

from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import ExpenseForm
from .models import Expense


def dashboard(request):
    today = timezone.localdate()

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense logged successfully.')
            return redirect('expenses:dashboard')
    else:
        form = ExpenseForm(initial={'spent_on': today})

    today_expenses = Expense.objects.filter(spent_on=today)

    totals_map = {
        row['category']: row['total_amount']
        for row in today_expenses.values('category').annotate(
            total_amount=Coalesce(Sum('amount'), Decimal('0.00'))
        )
    }

    category_totals = {
        'food': totals_map.get(Expense.CATEGORY_FOOD, Decimal('0.00')),
        'rent': totals_map.get(Expense.CATEGORY_RENT, Decimal('0.00')),
        'fun': totals_map.get(Expense.CATEGORY_FUN, Decimal('0.00')),
    }
    daily_total = sum(category_totals.values(), Decimal('0.00'))

    import json

    context = {
        'form': form,
        'today': today,
        'category_totals': category_totals,
        'category_totals_json': json.dumps(category_totals, cls=DjangoJSONEncoder),
        'daily_total': daily_total,
        # Pull only fields rendered in the template for a lighter query.
        'recent_entries': today_expenses.only('category', 'amount', 'spent_on').order_by('-created_at')[:5],
    }
    return render(request, 'expenses/index.html', context)
