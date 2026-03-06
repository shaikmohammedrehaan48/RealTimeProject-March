from django.contrib import admin

from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
	list_display = ('category', 'amount', 'spent_on', 'created_at')
	list_filter = ('category', 'spent_on')
	search_fields = ('category',)
