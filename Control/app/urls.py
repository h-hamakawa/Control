from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('detail/', views.detail_view, name='detail'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('management/', views.management_view, name='management'),
    path('management/income/', views.income_view, name='income'),
    path('management/expense/', views.expense_view, name='expense'),
    path('management/credit/', views.credit_view, name='credit'),
    path('management/reset/', views.reset_possession_view, name='reset_possession'),
    path('management/debt/', views.debt_setting_view, name='debt_setting'),
    path('management/debt/delete/<int:debt_id>/', views.delete_debt_view, name='delete_debt'),
    path('management/salary/', views.salary_setting_view, name='salary_setting'),

    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/', views.calendar_events_api, name='calendar_events_api'),
    path('calendar/add/', views.add_event_view, name='add_event'),
    path('calendar/delete/<int:event_id>/', views.delete_event_view, name='delete_event'),

    path('history/', views.history_view, name='history'),

    path('settings/', views.settings_view, name='settings'),
    path('settings/salary/', views.salary_day_settings_view, name='salary_day_settings'),
    path('settings/credit/', views.credit_card_settings_view, name='credit_card_settings'),
    path('settings/credit/add/', views.add_credit_card_view, name='add_credit_card'),
    path('settings/credit/delete/<int:card_id>/', views.delete_credit_card_view, name='delete_credit_card'),
    path('settings/password/', views.password_change_view, name='password_change'),
    path('settings/category/', views.category_settings_view, name='category_settings'),
    path('settings/category/add/', views.add_category_view, name='add_category'),
    path('settings/category/edit/<int:category_id>/', views.edit_category_view, name='edit_category'),
    path('settings/category/delete/<int:category_id>/', views.delete_category_view, name='delete_category'),
]
