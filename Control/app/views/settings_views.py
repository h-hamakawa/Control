from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import UserProfile, CreditCard, Category
from ..forms import (
    SalaryDayForm, CreditCardForm, PasswordChangeForm, CategoryForm
)


@login_required
def settings_view(request):
    return render(request, 'settings.html')


@login_required
def salary_day_settings_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = SalaryDayForm(request.POST)
        if form.is_valid():
            profile.salary_type = form.cleaned_data['salary_type']
            profile.salary_day = form.cleaned_data.get('salary_day')
            profile.save()
            messages.success(request, '給料日設定を保存しました')
            return redirect('settings')
    else:
        form = SalaryDayForm(initial={
            'salary_type': profile.salary_type,
            'salary_day': profile.salary_day,
        })
    return render(request, 'settings_salary.html', {'form': form, 'profile': profile})


@login_required
def credit_card_settings_view(request):
    cards = CreditCard.objects.filter(user=request.user)
    return render(request, 'settings_credit.html', {'cards': cards})


@login_required
def add_credit_card_view(request):
    if request.method == 'POST':
        form = CreditCardForm(request.POST)
        if form.is_valid():
            card = form.save(commit=False)
            card.user = request.user
            card.save()
            messages.success(request, f'{card.name} を追加しました')
            return redirect('credit_card_settings')
    else:
        form = CreditCardForm()
    return render(request, 'settings_credit_add.html', {'form': form})


@login_required
def delete_credit_card_view(request, card_id):
    card = get_object_or_404(CreditCard, id=card_id, user=request.user)
    if request.method == 'POST':
        card.delete()
        messages.success(request, f'{card.name} を削除しました')
    return redirect('credit_card_settings')


@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['current_password']):
                messages.error(request, '現在のパスワードが正しくありません')
            else:
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, 'パスワードを変更しました')
                return redirect('settings')
    else:
        form = PasswordChangeForm()
    return render(request, 'settings_password.html', {'form': form})


@login_required
def category_settings_view(request):
    income_categories = Category.objects.filter(user=request.user, category_type=Category.INCOME)
    expense_categories = Category.objects.filter(user=request.user, category_type=Category.EXPENSE)
    return render(request, 'settings_category.html', {
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    })


@login_required
def add_category_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()
            messages.success(request, f'カテゴリ「{category.name}」を追加しました')
            return redirect('category_settings')
    else:
        form = CategoryForm()
    return render(request, 'settings_category_add.html', {'form': form})


@login_required
def edit_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'カテゴリを更新しました')
            return redirect('category_settings')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'settings_category_edit.html', {'form': form, 'category': category})


@login_required
def delete_category_view(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'カテゴリを削除しました')
    return redirect('category_settings')
