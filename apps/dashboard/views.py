import hashlib
import random
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

import pytz
from django.db.models import Count, F
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

        health_tip = self._get_health_tip(user_id=user.id, selected_date=selected_date)
        reminders_summary = self._get_reminders_summary(user)
        medicine_summary = self._get_medicine_summary(user)
        upcoming_refills = self._get_upcoming_refills(user)

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

    def _get_reminders_summary(self, user):
        total = Reminder.objects.filter(user=user).count()
        active = Reminder.objects.filter(user=user, is_active=True).count()
        inactive = total - active

        return {
            'total': total,
            'active': active,
            'inactive': inactive,
        }

    def _get_medicine_summary(self, user):
        counts = Reminder.objects.filter(user=user, is_active=True).values('medicine_type').annotate(
            count=Count('id')
        )
        count_map = {row['medicine_type']: row['count'] for row in counts}

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

    def _get_upcoming_refills(self, user):
        reminders = Reminder.objects.filter(
            user=user,
            refill_reminder=True,
        ).prefetch_related('dose_schedules').order_by('quantity')

        upcoming = []
        for reminder in reminders:
            daily_amount = sum(
                (Decimal(str(dose.amount)) for dose in reminder.dose_schedules.all()),
                Decimal('0'),
            )

            days_left = None
            if daily_amount > 0:
                raw_days = reminder.quantity / daily_amount
                if raw_days < 0:
                    raw_days = Decimal('0')
                days_left = raw_days.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            upcoming.append({
                'id': reminder.id,
                'medicine_name': reminder.medicine_name,
                'medicine_type': reminder.medicine_type,
                'medicine_type_label': reminder.get_medicine_type_display(),
                'quantity': str(reminder.quantity),
                'refill_threshold': str(reminder.refill_threshold),
                'daily_amount': str(daily_amount) if daily_amount > 0 else None,
                'days_left_estimate': str(days_left) if days_left is not None else None,
                'is_active': reminder.is_active,
            })

        upcoming.sort(key=lambda item: (item['days_left_estimate'] is None, item['days_left_estimate'] or ''))
        return upcoming
