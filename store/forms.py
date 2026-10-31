from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    city = forms.CharField(max_length=100)
    state = forms.CharField(max_length=100)
    postal_code = forms.CharField(max_length=12, label="PIN code")
    gstin = forms.CharField(max_length=15, required=False, label="GSTIN (optional)")
    payment_method = forms.ChoiceField(choices=[("cod", "Cash on Delivery"), ("online", "Online payment (integration required)")])
    customer_note = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
