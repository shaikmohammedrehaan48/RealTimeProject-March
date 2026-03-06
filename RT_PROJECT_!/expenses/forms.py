from django import forms
from django.utils import timezone

from .models import Expense


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'spent_on']
        widgets = {
            'category': forms.Select(attrs={'class': 'field-input'}),
            'amount': forms.NumberInput(
                attrs={
                    'class': 'field-input',
                    'placeholder': '0.00',
                    'step': '0.01',
                    'min': '0.01',
                }
            ),
            'spent_on': forms.DateInput(attrs={'class': 'field-input', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = 'Choose category'
        self.fields['amount'].help_text = 'Use your local currency amount.'
        self.fields['spent_on'].initial = timezone.localdate()

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount
