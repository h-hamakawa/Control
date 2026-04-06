from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import datetime
import calendar


class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None):
        if not email:
            raise ValueError('メールアドレスは必須です')
        user = self.model(email=self.normalize_email(email), name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        user = self.create_user(email, name, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name='メールアドレス')
    name = models.CharField(max_length=100, verbose_name='氏名')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    class Meta:
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    SALARY_TYPE_FIXED = 'fixed'
    SALARY_TYPE_VARIABLE = 'variable'
    SALARY_TYPE_CHOICES = [
        (SALARY_TYPE_FIXED, '固定'),
        (SALARY_TYPE_VARIABLE, '変動'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    possession = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='所持金')
    scheduled_income = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='予定所持金')
    salary_type = models.CharField(max_length=10, choices=SALARY_TYPE_CHOICES, default=SALARY_TYPE_FIXED, verbose_name='給料日タイプ')
    salary_day = models.IntegerField(null=True, blank=True, verbose_name='給料日（固定）')
    next_salary_date = models.DateField(null=True, blank=True, verbose_name='次の給料日')
    last_payday_processed = models.DateField(null=True, blank=True, verbose_name='最終給料日処理日')

    class Meta:
        verbose_name = 'ユーザープロフィール'
        verbose_name_plural = 'ユーザープロフィール'

    def __str__(self):
        return f'{self.user.name}のプロフィール'

    def _next_salary_date_from_day(self, base_date, day):
        last_day = calendar.monthrange(base_date.year, base_date.month)[1]
        actual_day = min(day, last_day)
        if base_date.day < actual_day:
            return base_date.replace(day=actual_day)
        next_month = (base_date.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
        last_day_next = calendar.monthrange(next_month.year, next_month.month)[1]
        return next_month.replace(day=min(day, last_day_next))

    def get_next_salary_date(self):
        if self.salary_type == self.SALARY_TYPE_FIXED and self.salary_day:
            return self._next_salary_date_from_day(timezone.localdate(), self.salary_day)
        return self.next_salary_date

    def days_until_next_salary(self):
        next_date = self.get_next_salary_date()
        if next_date:
            return (next_date - timezone.localdate()).days
        return None

    def get_next_next_salary_date(self):
        next_date = self.get_next_salary_date()
        if next_date is None:
            return None
        if self.salary_type == self.SALARY_TYPE_FIXED and self.salary_day:
            return self._next_salary_date_from_day(
                next_date + datetime.timedelta(days=1), self.salary_day
            )
        return None

    def days_until_next_next_salary(self):
        next_next_date = self.get_next_next_salary_date()
        if next_next_date:
            return (next_next_date - timezone.localdate()).days
        return None


class Category(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    TYPE_CHOICES = [
        (INCOME, '収益'),
        (EXPENSE, '費用'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=50, verbose_name='カテゴリ名')
    category_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='種別')

    class Meta:
        verbose_name = 'カテゴリ'
        verbose_name_plural = 'カテゴリ'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_category_type_display()})'


class CreditCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='credit_cards')
    name = models.CharField(max_length=50, verbose_name='カード名')
    payment_day = models.IntegerField(verbose_name='支払い日')
    closing_day = models.IntegerField(verbose_name='締め日')

    class Meta:
        verbose_name = 'クレジットカード'
        verbose_name_plural = 'クレジットカード'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_credit_debt(self):
        return self.transactions.filter(
            transaction_type=Transaction.CREDIT,
            credit_settled=False
        ).aggregate(total=models.Sum('amount'))['total'] or 0


class Transaction(models.Model):
    INCOME = 'income'
    EXPENSE = 'expense'
    CREDIT = 'credit'
    RESET = 'reset'
    SALARY = 'salary'

    TYPE_CHOICES = [
        (INCOME, '収益'),
        (EXPENSE, '費用'),
        (CREDIT, 'クレジット'),
        (RESET, '所持金再設定'),
        (SALARY, '給料'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='記録日時')
    transaction_date = models.DateField(default=timezone.localdate, verbose_name='取引日')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='金額')
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='種別')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='カテゴリ')
    credit_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions', verbose_name='クレジットカード')
    credit_settled = models.BooleanField(default=False, verbose_name='精算済み')
    note = models.CharField(max_length=200, blank=True, verbose_name='備考')
    possession_after = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='取引後所持金')

    class Meta:
        verbose_name = '取引履歴'
        verbose_name_plural = '取引履歴'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_transaction_type_display()} {self.amount}円 ({self.transaction_date})'


class Debt(models.Model):
    CURRENT = 'current'
    NEXT = 'next'
    PERIOD_CHOICES = [
        (CURRENT, '負債（今期）'),
        (NEXT, '予定負債（来期）'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='金額')
    description = models.CharField(max_length=200, verbose_name='説明')
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default=CURRENT, verbose_name='期間')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='登録日時')

    class Meta:
        verbose_name = '負債'
        verbose_name_plural = '負債'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.description} {self.amount}円 ({self.get_period_display()})'


class CalendarEvent(models.Model):
    GENERAL = 'general'
    SALARY = 'salary'
    PAYMENT = 'payment'
    INCOME_EVENT = 'income'

    EVENT_TYPE_CHOICES = [
        (GENERAL, '一般'),
        (SALARY, '給料日'),
        (PAYMENT, '支払い'),
        (INCOME_EVENT, '収入'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calendar_events')
    event_date = models.DateField(verbose_name='日付')
    title = models.CharField(max_length=100, verbose_name='タイトル')
    amount = models.DecimalField(max_digits=12, decimal_places=0, null=True, blank=True, verbose_name='金額')
    event_type = models.CharField(max_length=10, choices=EVENT_TYPE_CHOICES, default=GENERAL, verbose_name='種別')
    is_processed = models.BooleanField(default=False, verbose_name='処理済み')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='カテゴリ')

    class Meta:
        verbose_name = 'カレンダーイベント'
        verbose_name_plural = 'カレンダーイベント'
        ordering = ['event_date']

    def __str__(self):
        return f'{self.event_date} {self.title}'
