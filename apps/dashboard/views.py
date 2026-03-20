import hashlib
import random
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import pytz
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.reminders.models import Reminder
from utils.responses import StandardResponse
from .models import HealthTip


class DashboardView(APIView):
    """Aggregated dashboard data for the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_param = request.query_params.get('date')
        if date_param:
            try:
                selected_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            except ValueError:
                return StandardResponse.error(
                    message='Invalid date format. Use YYYY-MM-DD',
                    status_code=400,
                )
        else:
            user_tz = self._get_user_timezone(request.user)
            selected_date = timezone.now().astimezone(user_tz).date()

        user = request.user
        current_local_date = timezone.now().astimezone(self._get_user_timezone(user)).date()
        reminder_states = self._get_reminder_states(
            user=user,
            selected_date=selected_date,
            current_local_date=current_local_date,
        )

        health_tip = self._get_health_tip(user_id=user.id, selected_date=selected_date)
        reminders_summary = self._get_reminders_summary(reminder_states)
        medicine_summary = self._get_medicine_summary(reminder_states)
        upcoming_refills = self._get_upcoming_refills(reminder_states)

        return StandardResponse.success(data={
            'selected_date': str(selected_date),
            'health_tip': health_tip,
            'upcoming_refills': {
                'count': len(upcoming_refills),
                'items': upcoming_refills,
            },
            'reminders_summary': reminders_summary,
            'medicine_summary': medicine_summary,
        })

    def _get_user_timezone(self, user):
        try:
            return pytz.timezone(user.timezone)
        except Exception:
            return pytz.UTC

    def _get_health_tip(self, user_id, selected_date):
        tips = list(
            HealthTip.objects.filter(is_active=True)
            .values('id', 'title', 'content', 'source')
        )

        if not tips:
            return None

        seed_source = f"{user_id}:{selected_date.isoformat()}"
        seed = int(hashlib.sha256(seed_source.encode('utf-8')).hexdigest(), 16)
        rng = random.Random(seed)
        tip = rng.choice(tips)
        tip['date'] = str(selected_date)
        return tip

    def _get_reminder_states(self, user, selected_date, current_local_date):
        reminders = Reminder.objects.filter(user=user).prefetch_related('dose_schedules')
        reminder_states = []

        for reminder in reminders:
            daily_amount = sum(
                (Decimal(str(dose.amount)) for dose in reminder.dose_schedules.all()),
                Decimal('0'),
            )
            projected_quantity = self._get_projected_quantity(
                reminder=reminder,
                daily_amount=daily_amount,
                selected_date=selected_date,
                current_local_date=current_local_date,
            )
            days_left = self._get_days_left(projected_quantity, daily_amount)
            is_active_on_selected_date = (
                reminder.is_active
                and reminder.start_date <= selected_date
                and projected_quantity > 0
            )

            reminder_states.append({
                'reminder': reminder,
                'daily_amount': daily_amount,
                'projected_quantity': projected_quantity,
                'days_left_estimate': days_left,
                'is_active_on_selected_date': is_active_on_selected_date,
            })

        return reminder_states

    def _get_projected_quantity(self, reminder, daily_amount, selected_date, current_local_date):
        projected_quantity = reminder.quantity

        if selected_date > current_local_date and daily_amount > 0:
            projection_start_date = max(current_local_date, reminder.start_date)
            projected_days = max((selected_date - projection_start_date).days, 0)
            projected_quantity -= daily_amount * projected_days

        if projected_quantity < 0:
            return Decimal('0')

        return projected_quantity

    def _get_days_left(self, quantity, daily_amount):
        if daily_amount <= 0 or quantity <= 0:
            return None

        return (quantity / daily_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_reminders_summary(self, reminder_states):
        total = len(reminder_states)
        active = sum(1 for state in reminder_states if state['is_active_on_selected_date'])
        inactive = total - active

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
        }

    def _get_medicine_summary(self, reminder_states):
        count_map = {}
        for state in reminder_states:
            if not state['is_active_on_selected_date']:
                continue

            medicine_type = state['reminder'].medicine_type
            count_map[medicine_type] = count_map.get(medicine_type, 0) + 1

        summary = []
        for code, label in Reminder.MEDICINE_TYPE_CHOICES:
            summary.append({
                'medicine_type': code,
                'label': label,
                'count': count_map.get(code, 0),
            })

        return {
            'active_only': True,
            'items': summary,
        }

    def _get_upcoming_refills(self, reminder_states):
        upcoming = []
        for state in reminder_states:
            reminder = state['reminder']
            if not reminder.refill_reminder or not state['is_active_on_selected_date']:
                continue

            upcoming.append({
                'id': reminder.id,
                'medicine_name': reminder.medicine_name,
                'medicine_type': reminder.medicine_type,
                'medicine_type_label': reminder.get_medicine_type_display(),
                'quantity': str(state['projected_quantity']),
                'refill_threshold': str(reminder.refill_threshold),
                'daily_amount': str(state['daily_amount']) if state['daily_amount'] > 0 else None,
                'days_left_estimate': (
                    str(state['days_left_estimate'])
                    if state['days_left_estimate'] is not None else None
                ),
                'is_active': state['is_active_on_selected_date'],
            })

        upcoming.sort(
            key=lambda item: (
                item['days_left_estimate'] is None,
                Decimal(item['days_left_estimate']) if item['days_left_estimate'] is not None else Decimal('Infinity'),
                item['medicine_name'].lower(),
            )
        )
        return upcoming
