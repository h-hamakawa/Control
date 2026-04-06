from django.utils import timezone
from .models import UserProfile, Transaction, Debt, CalendarEvent, Category


class PaydayProcessingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            self._process_payday(request.user)
            self._process_calendar_events(request.user)
        return self.get_response(request)

    def _process_payday(self, user):
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return

        today = timezone.localdate()
        next_salary_date = profile.get_next_salary_date()

        if next_salary_date is None:
            return

        if today < next_salary_date:
            return

        if profile.last_payday_processed and profile.last_payday_processed >= next_salary_date:
            return

        if profile.scheduled_income > 0:
            new_possession = profile.possession + profile.scheduled_income
            Transaction.objects.create(
                user=user,
                transaction_date=next_salary_date,
                amount=profile.scheduled_income,
                transaction_type=Transaction.SALARY,
                note='給料自動受取',
                possession_after=new_possession,
            )
            profile.possession = new_possession
            profile.scheduled_income = 0

        Debt.objects.filter(user=user, period=Debt.NEXT).update(period=Debt.CURRENT)

        profile.last_payday_processed = today

        if profile.salary_type == UserProfile.SALARY_TYPE_FIXED and profile.salary_day:
            import calendar as cal
            import datetime
            next_month = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
            last_day = cal.monthrange(next_month.year, next_month.month)[1]
            profile.next_salary_date = next_month.replace(day=min(profile.salary_day, last_day))
        else:
            profile.next_salary_date = None

        profile.save()

    def _process_calendar_events(self, user):
        today = timezone.localdate()
        pending_events = CalendarEvent.objects.filter(
            user=user,
            event_date__lte=today,
            is_processed=False,
        ).exclude(event_type=CalendarEvent.GENERAL).exclude(amount__isnull=True)

        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            return

        for event in pending_events:
            if event.event_type == CalendarEvent.SALARY:
                new_possession = profile.possession + event.amount
                Transaction.objects.create(
                    user=user,
                    transaction_date=event.event_date,
                    amount=event.amount,
                    transaction_type=Transaction.SALARY,
                    category=event.category,
                    note=event.title,
                    possession_after=new_possession,
                )
                profile.possession = new_possession
                Debt.objects.filter(user=user, period=Debt.NEXT).update(period=Debt.CURRENT)
                profile.last_payday_processed = today

                next_salary_event = CalendarEvent.objects.filter(
                    user=user,
                    event_type=CalendarEvent.SALARY,
                    event_date__gt=event.event_date,
                    is_processed=False,
                ).order_by('event_date').first()
                if next_salary_event:
                    profile.next_salary_date = next_salary_event.event_date
                else:
                    profile.next_salary_date = None

            elif event.event_type == CalendarEvent.PAYMENT:
                new_possession = profile.possession - event.amount
                Transaction.objects.create(
                    user=user,
                    transaction_date=event.event_date,
                    amount=event.amount,
                    transaction_type=Transaction.EXPENSE,
                    category=event.category,
                    note=event.title,
                    possession_after=new_possession,
                )
                profile.possession = new_possession

            elif event.event_type == CalendarEvent.INCOME_EVENT:
                new_possession = profile.possession + event.amount
                Transaction.objects.create(
                    user=user,
                    transaction_date=event.event_date,
                    amount=event.amount,
                    transaction_type=Transaction.INCOME,
                    category=event.category,
                    note=event.title,
                    possession_after=new_possession,
                )
                profile.possession = new_possession

            event.is_processed = True
            event.save()

        profile.save()
