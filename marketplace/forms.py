from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Product

_INPUT = (
    'w-full border-2 border-green-300 rounded-2xl px-4 py-3 '
    'text-lg font-medium focus:outline-none focus:border-green-600 '
    'focus:ring-2 focus:ring-green-100 transition bg-white'
)

_SELECT = (
    'w-full border-2 border-green-300 rounded-2xl px-4 py-3 '
    'text-lg font-medium focus:outline-none focus:border-green-600 bg-white'
)


class RegisterForm(UserCreationForm):
    phone = forms.CharField(
        max_length=15, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'e.g. 9876543210'}),
    )
    # Village is optional but useful for Kisan Mitra personalisation
    village = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Your village / district'}),
    )

    class Meta:
        model  = User
        fields = ('username', 'phone', 'village', 'role', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Choose a username'}),
            'role':     forms.Select(attrs={'class': _SELECT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fn in ('password1', 'password2'):
            self.fields[fn].widget.attrs.update({
                'class':       _INPUT,
                'placeholder': 'Password' if fn == 'password1' else 'Confirm password',
            })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone   = self.cleaned_data.get('phone', '')
        user.village = self.cleaned_data.get('village', '')
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': _INPUT, 'placeholder': 'Your username'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': _INPUT, 'placeholder': 'Your password'}),
    )


class ProductForm(forms.ModelForm):
    class Meta:
        model  = Product
        fields = ('crop_name', 'quantity', 'price', 'location', 'harvest_date', 'image')
        widgets = {
            'crop_name': forms.TextInput(attrs={
                'class':       _INPUT,
                'placeholder': 'e.g. Tomato, Wheat, Rice',
            }),
            'quantity': forms.NumberInput(attrs={
                'class':       _INPUT,
                'placeholder': 'Enter quantity in KG',
                'id':          'id_quantity',
                'min':         '1',
            }),
            'price': forms.NumberInput(attrs={
                'class':       _INPUT,
                'placeholder': 'Price per KG in ₹',
                'min':         '1',
            }),
            'location': forms.TextInput(attrs={
                'class':       _INPUT,
                'placeholder': 'Your village / city / district',
            }),
            'harvest_date': forms.DateInput(attrs={
                'type':  'date',
                'class': (
                    'w-full border-4 border-green-300 rounded-2xl p-5 text-2xl '
                    'font-bold cursor-pointer focus:outline-none focus:border-green-600 '
                    'focus:ring-4 focus:ring-green-100 transition bg-white '
                    'tracking-wide text-gray-700'
                ),
            }),
            'image': forms.FileInput(attrs={
                'class': (
                    'w-full border-2 border-dashed border-green-300 rounded-2xl px-4 py-3 '
                    'text-base text-gray-500 cursor-pointer bg-green-50 '
                    'hover:bg-green-100 transition'
                ),
                'accept': 'image/*',  # restrict to images in browser file picker
            }),
        }

    def clean_quantity(self):
        qty = self.cleaned_data.get('quantity')
        if qty is not None and qty <= 0:
            raise forms.ValidationError('Quantity must be greater than 0.')
        return qty

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise forms.ValidationError('Price must be greater than 0.')
        return price