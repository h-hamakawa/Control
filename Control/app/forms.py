from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, UserProfile, Category, CreditCard, Transaction, Debt, CalendarEvent


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='メールアドレス',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@email.com', 'autofocus': True})
    )
    password = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'パスワード'})
    )


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'パスワード'})
    )
    password2 = forms.CharField(
        label='パスワード（確認）',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'パスワードを再入力'})
    )

    class Meta:
        model = User
        fields = ['email', 'name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'example@email.com'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '氏名'}),
        }
        labels = {
            'email': 'メールアドレス',
            'name': '氏名',
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('パスワードが一致しません')
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='現在のパスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )
    new_password1 = forms.CharField(
        label='新しいパスワード',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )
    new_password2 = forms.CharField(
        label='新しいパスワード（確認）',
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    def clean_new_password2(self):
        p1 = self.cleaned_data.get('new_password1')
        p2 = self.cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('パスワードが一致しません')
        return p2


class IncomeForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'note', 'transaction_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '金額'}),
            'note': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '備考（任意）'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
        labels = {
            'category': 'カテゴリ',
            'amount': '金額',
            'note': '備考',
            'transaction_date': '日付',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, category_type=Category.INCOME)
        self.fields['category'].widget.attrs['class'] = 'form-input'
        self.fields['category'].empty_label = 'カテゴリを選択'


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['category', 'amount', 'note', 'transaction_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '金額'}),
            'note': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '備考（任意）'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
        labels = {
            'category': 'カテゴリ',
            'amount': '金額',
            'note': '備考',
            'transaction_date': '日付',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user, category_type=Category.EXPENSE)
        self.fields['category'].widget.attrs['class'] = 'form-input'
        self.fields['category'].empty_label = 'カテゴリを選択'


class CreditForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['credit_card', 'category', 'amount', 'note', 'transaction_date']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '金額'}),
            'note': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '備考（任意）'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
        }
        labels = {
            'credit_card': 'クレジットカード',
            'category': 'カテゴリ',
            'amount': '金額',
            'note': '備考',
            'transaction_date': '日付',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['credit_card'].queryset = CreditCard.objects.filter(user=user)
        self.fields['credit_card'].widget.attrs['class'] = 'form-input'
        self.fields['credit_card'].empty_label = 'カードを選択'
        self.fields['category'].queryset = Category.objects.filter(user=user, category_type=Category.EXPENSE)
        self.fields['category'].widget.attrs['class'] = 'form-input'
        self.fields['category'].empty_label = 'カテゴリを選択（任意）'
        self.fields['category'].required = False


class ResetPossessionForm(forms.Form):
    actual_amount = forms.DecimalField(
        label='実際の所持金',
        max_digits=12,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '現在持っているお金'})
    )
    note = forms.CharField(
        label='備考',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '備考（任意）'})
    )


class DebtSettingForm(forms.Form):
    credit_card = forms.ModelChoiceField(
        label='クレジットカード',
        queryset=CreditCard.objects.none(),
        widget=forms.Select(attrs={'class': 'form-input'})
    )
    confirmed_amount = forms.DecimalField(
        label='確定金額',
        max_digits=12,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '請求確定額'})
    )
    description = forms.CharField(
        label='説明',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '説明（任意）'})
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['credit_card'].queryset = CreditCard.objects.filter(user=user)
        self.fields['credit_card'].empty_label = 'カードを選択'


class ManualDebtForm(forms.ModelForm):
    class Meta:
        model = Debt
        fields = ['amount', 'description', 'period']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '金額'}),
            'description': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '内容'}),
            'period': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'amount': '金額',
            'description': '内容',
            'period': '期間',
        }


class SalarySettingForm(forms.Form):
    amount = forms.DecimalField(
        label='給料金額',
        max_digits=12,
        decimal_places=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '次の給料金額'})
    )


class SalaryDayForm(forms.Form):
    SALARY_TYPE_CHOICES = [
        ('fixed', '固定'),
        ('variable', '変動'),
    ]
    salary_type = forms.ChoiceField(
        label='給料日タイプ',
        choices=SALARY_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'radio-input'})
    )
    salary_day = forms.IntegerField(
        label='給料日（固定の場合）',
        required=False,
        min_value=1,
        max_value=31,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '例: 25'})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('salary_type') == 'fixed' and not cleaned.get('salary_day'):
            raise forms.ValidationError('固定の場合は給料日を入力してください')
        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'category_type']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'カテゴリ名'}),
            'category_type': forms.Select(attrs={'class': 'form-input'}),
        }
        labels = {
            'name': 'カテゴリ名',
            'category_type': '種別',
        }


class CreditCardForm(forms.ModelForm):
    class Meta:
        model = CreditCard
        fields = ['name', 'payment_day', 'closing_day']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'カード名'}),
            'payment_day': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '例: 27', 'min': 1, 'max': 31}),
            'closing_day': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '例: 15', 'min': 1, 'max': 31}),
        }
        labels = {
            'name': 'カード名',
            'payment_day': '支払い日',
            'closing_day': '締め日',
        }


class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['event_date', 'title', 'event_type', 'amount', 'category']
        widgets = {
            'event_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'タイトル'}),
            'event_type': forms.Select(attrs={'class': 'form-input'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '金額（任意）'}),
        }
        labels = {
            'event_date': '日付',
            'title': 'タイトル',
            'event_type': '種別',
            'amount': '金額',
            'category': 'カテゴリ',
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(user=user)
        self.fields['category'].widget.attrs['class'] = 'form-input'
        self.fields['category'].empty_label = 'カテゴリを選択（任意）'
        self.fields['category'].required = False
        self.fields['amount'].required = False
