from .auth_views import login_view, logout_view, register_view
from .home_views import home_view, detail_view
from .management_views import (
    management_view, income_view, expense_view, credit_view,
    reset_possession_view, debt_setting_view, salary_setting_view,
    delete_debt_view
)
from .calendar_views import calendar_view, calendar_events_api, add_event_view, delete_event_view
from .history_views import history_view
from .settings_views import (
    settings_view, salary_day_settings_view, credit_card_settings_view,
    add_credit_card_view, delete_credit_card_view, password_change_view,
    category_settings_view, add_category_view, delete_category_view,
    edit_category_view
)
