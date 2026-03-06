from django.db import models


class Expense(models.Model):
	CATEGORY_FOOD = 'food'
	CATEGORY_RENT = 'rent'
	CATEGORY_FUN = 'fun'

	CATEGORY_CHOICES = [
		(CATEGORY_FOOD, 'Food'),
		(CATEGORY_RENT, 'Rent'),
		(CATEGORY_FUN, 'Fun'),
	]

	category = models.CharField(max_length=12, choices=CATEGORY_CHOICES)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	spent_on = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-spent_on', '-created_at']
		indexes = [
			models.Index(fields=['spent_on', 'category']),
		]

	def __str__(self):
		return f"{self.get_category_display()} - {self.amount} on {self.spent_on}"
