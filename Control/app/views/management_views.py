from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from ..models import UserProfile, Transaction, Debt, CreditCard
from ..forms import (
    IncomeForm, ExpenseForm, CreditForm, ResetPossessionForm,
    DebtSettingForm, ManualDebtForm, SalarySettingForm
)


@login_required
def management_view(request):
    return render(request, 'management.html')


@login_required
def income_view(request):
    if request.method == 'POST':
        form = IncomeForm(request.user, request.POST)
        if form.is_valid():
            profile = request.user.profile
            amount = form.cleaned_data['amount']
            new_possession = profile.possession + amount
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_type = Transaction.INCOME
            transaction.possession_after = new_possession
            transaction.save()
            profile.possession = new_possession
            profile.save()
            messages.success(request, f'収益 ¥{int(amount):,} を追加しました')
            return redirect('management')
    else:
        form = IncomeForm(request.user, initial={'transaction_date': timezone.localdate()})
    return render(request, 'management_income.html', {'form': form})


@login_required
def expense_view(request):
    if request.method == 'POST':
        form = ExpenseForm(request.user, request.POST)
        if form.is_valid():
            profile = request.user.profile
            amount = form.cleaned_data['amount']
            new_possession = profile.possession - amount
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_type = Transaction.EXPENSE
            transaction.possession_after = new_possession
            transaction.save()
            profile.possession = new_possession
            profile.save()
            messages.success(request, f'費用 ¥{int(amount):,} を追加しました')
            return redirect('management')
    else:
        form = ExpenseForm(request.user, initial={'transaction_date': timezone.localdate()})
    return render(request, 'management_expense.html', {'form': form})


@login_required
def credit_view(request):
    if request.method == 'POST':
        form = CreditForm(request.user, request.POST)
        if form.is_valid():
            profile = request.user.profile
            amount = form.cleaned_data['amount']
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.transaction_type = Transaction.CREDIT
            transaction.possession_after = profile.possession
            transaction.save()
            messages.success(request, f'クレジット ¥{int(amount):,} を追加しました')
            return redirect('management')
    else:
        form = CreditForm(request.user, initial={'transaction_date': timezone.localdate()})
    return render(request, 'management_credit.html', {'form': form})


@login_required
def reset_possession_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = ResetPossessionForm(request.POST)
        if form.is_valid():
            actual = form.cleaned_data['actual_amount']
            note = form.cleaned_data.get('note', '')
            diff = actual - profile.possession
            if diff != 0:
                transaction_type = Transaction.INCOME if diff > 0 else Transaction.EXPENSE
                Transaction.objects.create(
                    user=request.user,
                    transaction_date=timezone.localdate(),
                    amount=abs(diff),
                    transaction_type=transaction_type,
                    note=f'現金過不足{(" " + note) if note else ""}',
                    possession_after=actual,
                )
            profile.possession = actual
            profile.save()
            messages.success(request, f'所持金を ¥{int(actual):,} に再設定しました')
            return redirect('management')
    else:
        form = ResetPossessionForm(initial={'actual_amount': profile.possession})
    return render(request, 'management_reset.html', {'form': form, 'current_possession': profile.possession})


@login_required
def debt_setting_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'settle_credit':
            form = DebtSettingForm(request.user, request.POST)
            manual_form = ManualDebtForm()
            if form.is_valid():
                card = form.cleaned_data['credit_card']
                confirmed = form.cleaned_data['confirmed_amount']
                desc = form.cleaned_data.get('description') or f'{card.name} 請求確定'
                Transaction.objects.filter(
                    user=request.user,
                    credit_card=card,
                    transaction_type=Transaction.CREDIT,
                    credit_settled=False
                ).update(credit_settled=True)
                Debt.objects.create(
                    user=request.user,
                    amount=confirmed,
                    description=desc,
                    period=Debt.CURRENT,
                )
                messages.success(request, f'{card.name} のクレジット負債を ¥{int(confirmed):,} で確定しました')
                return redirect('management')
        elif action == 'add_manual_debt':
            manual_form = ManualDebtForm(request.POST)
            form = DebtSettingForm(request.user)
            if manual_form.is_valid():
                debt = manual_form.save(commit=False)
                debt.user = request.user
                debt.save()
                messages.success(request, f'負債 ¥{int(debt.amount):,} を追加しました')
                return redirect('management')
        else:
            form = DebtSettingForm(request.user)
            manual_form = ManualDebtForm()
    else:
        form = DebtSettingForm(request.user)
        manual_form = ManualDebtForm()

    credit_cards = CreditCard.objects.filter(user=request.user)
    card_debts = []
    for card in credit_cards:
        debt = card.get_credit_debt()
        if debt > 0:
            card_debts.append({'card': card, 'amount': debt})

    context = {
        'form': form,
        'manual_form': manual_form,
        'card_debts': card_debts,
        'current_debts': Debt.objects.filter(user=request.user, period=Debt.CURRENT),
        'next_debts': Debt.objects.filter(user=request.user, period=Debt.NEXT),
    }
    return render(request, 'management_debt.html', context)


@login_required
def delete_debt_view(request, debt_id):
    debt = get_object_or_404(Debt, id=debt_id, user=request.user)
    if request.method == 'POST':
        debt.delete()
        messages.success(request, '負債を削除しました')
    return redirect('debt_setting')


@login_required
def salary_setting_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = SalarySettingForm(request.POST)
        if form.is_valid():
            profile.scheduled_income = form.cleaned_data['amount']
            profile.save()
            messages.success(request, f'予定給料を ¥{int(form.cleaned_data["amount"]):,} に設定しました')
            return redirect('management')
    else:
        form = SalarySettingForm(initial={'amount': profile.scheduled_income})
    return render(request, 'management_salary.html', {'form': form, 'profile': profile})
