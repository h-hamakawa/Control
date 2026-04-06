from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.utils import timezone
from ..models import UserProfile, Transaction, Debt, CreditCard
import json
import datetime


def get_financial_summary(user):
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return None

    credit_debt_total = Transaction.objects.filter(
        user=user,
        transaction_type=Transaction.CREDIT,
        credit_settled=False
    ).aggregate(total=Sum('amount'))['total'] or 0

    current_debt_total = Debt.objects.filter(
        user=user, period=Debt.CURRENT
    ).aggregate(total=Sum('amount'))['total'] or 0

    next_debt_total = Debt.objects.filter(
        user=user, period=Debt.NEXT
    ).aggregate(total=Sum('amount'))['total'] or 0

    possession = profile.possession
    scheduled_income = profile.scheduled_income
    usable = possession - credit_debt_total - current_debt_total
    planned_usable = usable + scheduled_income - next_debt_total

    credit_cards = CreditCard.objects.filter(user=user)
    card_debts = []
    for card in credit_cards:
        debt = card.get_credit_debt()
        if debt > 0:
            card_debts.append({'name': card.name, 'amount': debt})

    current_debts = Debt.objects.filter(user=user, period=Debt.CURRENT)
    next_debts = Debt.objects.filter(user=user, period=Debt.NEXT)

    return {
        'possession': possession,
        'credit_debt_total': credit_debt_total,
        'current_debt_total': current_debt_total,
        'next_debt_total': next_debt_total,
        'scheduled_income': scheduled_income,
        'usable': usable,
        'planned_usable': planned_usable,
        'days_until_next_salary': profile.days_until_next_salary(),
        'days_until_next_next_salary': profile.days_until_next_next_salary(),
        'next_salary_date': profile.get_next_salary_date(),
        'next_next_salary_date': profile.get_next_next_salary_date(),
        'card_debts': card_debts,
        'current_debts': current_debts,
        'next_debts': next_debts,
    }


@login_required
def home_view(request):
    summary = get_financial_summary(request.user)
    return render(request, 'home.html', {'summary': summary})


@login_required
def detail_view(request):
    today = timezone.localdate()
    thirty_days_ago = today - datetime.timedelta(days=30)

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__gte=thirty_days_ago
    ).order_by('transaction_date')

    daily_data = {}
    for t in transactions:
        date_str = t.transaction_date.strftime('%Y-%m-%d')
        if date_str not in daily_data:
            daily_data[date_str] = {'income': 0, 'expense': 0, 'credit': 0}
        if t.transaction_type in [Transaction.INCOME, Transaction.SALARY]:
            daily_data[date_str]['income'] += int(t.amount)
        elif t.transaction_type in [Transaction.EXPENSE, Transaction.RESET]:
            daily_data[date_str]['expense'] += int(t.amount)
        elif t.transaction_type == Transaction.CREDIT:
            daily_data[date_str]['credit'] += int(t.amount)

    dates = sorted(daily_data.keys())
    income_data = [daily_data[d]['income'] for d in dates]
    expense_data = [daily_data[d]['expense'] for d in dates]

    from django.db.models import Sum
    from ..models import Category

    category_expense = Transaction.objects.filter(
        user=request.user,
        transaction_type__in=[Transaction.EXPENSE, Transaction.CREDIT],
        transaction_date__gte=thirty_days_ago,
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')

    cat_labels = [item['category__name'] or 'カテゴリなし' for item in category_expense]
    cat_data = [int(item['total']) for item in category_expense]

    from django.db.models.functions import TruncMonth
    monthly = Transaction.objects.filter(
        user=request.user,
    ).annotate(month=TruncMonth('transaction_date')).values('month', 'transaction_type').annotate(
        total=Sum('amount')
    ).order_by('month')

    monthly_map = {}
    for item in monthly:
        month_str = item['month'].strftime('%Y-%m')
        if month_str not in monthly_map:
            monthly_map[month_str] = {'income': 0, 'expense': 0}
        if item['transaction_type'] in [Transaction.INCOME, Transaction.SALARY]:
            monthly_map[month_str]['income'] += int(item['total'])
        elif item['transaction_type'] in [Transaction.EXPENSE, Transaction.CREDIT]:
            monthly_map[month_str]['expense'] += int(item['total'])

    months = sorted(monthly_map.keys())[-12:]
    monthly_income = [monthly_map[m]['income'] for m in months]
    monthly_expense = [monthly_map[m]['expense'] for m in months]

    possession_history = Transaction.objects.filter(
        user=request.user,
        transaction_date__gte=thirty_days_ago
    ).order_by('transaction_date').values('transaction_date', 'possession_after')

    pos_dates = []
    pos_values = []
    for item in possession_history:
        pos_dates.append(item['transaction_date'].strftime('%Y-%m-%d'))
        pos_values.append(int(item['possession_after']))

    summary = get_financial_summary(request.user)

    context = {
        'summary': summary,
        'chart_dates': json.dumps(dates),
        'chart_income': json.dumps(income_data),
        'chart_expense': json.dumps(expense_data),
        'cat_labels': json.dumps(cat_labels),
        'cat_data': json.dumps(cat_data),
        'months': json.dumps(months),
        'monthly_income': json.dumps(monthly_income),
        'monthly_expense': json.dumps(monthly_expense),
        'pos_dates': json.dumps(pos_dates),
        'pos_values': json.dumps(pos_values),
    }
    return render(request, 'detail.html', context)
