

# AWTTAR Compare Calculator

from django import forms 

class tariff_form(forms.Form):
    fixed_tariff = forms.FloatField(
        label='Whats your Fixed Energy Tariff (€/MWh)',
        min_value=-200.,
        max_value=1000.,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50.0'})
    )
