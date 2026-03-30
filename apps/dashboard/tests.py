from datetime import date, datetime, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from rest_framework.test import APITestCase

from apps.dashboard.models import HealthTip
from apps.reminders.models import DoseSchedule, Reminder
from apps.users.models import CustomUser


class DashboardViewTests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='dashboard@example.com',
            password='testpass123',
            timezone='UTC',
        )
        self.client.force_authenticate(self.user)
        HealthTip.objects.create(
            title='Hydrate',
            content='Drink enough water.',
            source='Medialert',
            is_active=True,
        )

    def create_reminder(
        self,
        medicine_name,
        medicine_type,
        start_date,
        quantity,
        dose_amount,
        is_active=True,
        refill_reminder=False,
        refill_threshold=None,
    ):
        reminder = Reminder.objects.create(
            user=self.user,
            medicine_name=medicine_name,
            medicine_type=medicine_type,
            dose_count_daily=1,
            notification_methods=['whatsapp_message'],
            start_date=start_date,
            quantity=Decimal(quantity),
            initial_quantity=Decimal(quantity),
            refill_reminder=refill_reminder,
            refill_threshold=Decimal(refill_threshold) if refill_threshold is not None else None,
            is_active=is_active,
            
        )
        DoseSchedule.objects.create(
            reminder=reminder,
            dose_number=1,
            amount=Decimal(dose_amount),
            time='09:00:00',
        )
        return reminder

    @patch('apps.dashboard.views.timezone.now')
    def test_upcoming_refills_use_selected_date_projection(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 20, 9, 0, tzinfo=dt_timezone.utc)
        self.create_reminder(
            medicine_name='Amoxicillin',
            medicine_type='capsule',
            start_date=date(2026, 3, 10),
            quantity='5.00',
            dose_amount='1.00',
            refill_reminder=True,
            refill_threshold='2.00',
        )

        today_response = self.client.get('/api/dashboard/?date=2026-03-20')
        self.assertEqual(today_response.status_code, 200)
        self.assertEqual(today_response.data['data']['upcoming_refills']['count'], 1)
        today_item = today_response.data['data']['upcoming_refills']['items'][0]
        self.assertEqual(today_item['quantity'], '5.00')
        self.assertEqual(today_item['days_left_estimate'], '5.00')

        future_response = self.client.get('/api/dashboard/?date=2026-03-25')
        self.assertEqual(future_response.status_code, 200)
        self.assertEqual(future_response.data['data']['upcoming_refills']['count'], 0)
        self.assertEqual(future_response.data['data']['upcoming_refills']['items'], [])

    @patch('apps.dashboard.views.timezone.now')
    def test_summaries_change_for_selected_date(self, mock_now):
        mock_now.return_value = datetime(2026, 3, 20, 9, 0, tzinfo=dt_timezone.utc)
        self.create_reminder(
            medicine_name='Tablet A',
            medicine_type='tablet',
            start_date=date(2026, 3, 10),
            quantity='5.00',
            dose_amount='1.00',
        )
        self.create_reminder(
            medicine_name='Capsule B',
            medicine_type='capsule',
            start_date=date(2026, 3, 22),
            quantity='10.00',
            dose_amount='1.00',
        )
        self.create_reminder(
            medicine_name='Syrup C',
            medicine_type='syrup',
            start_date=date(2026, 3, 1),
            quantity='10.00',
            dose_amount='1.00',
            is_active=False,
        )

        today_response = self.client.get('/api/dashboard/?date=2026-03-20')
        self.assertEqual(today_response.status_code, 200)
        today_data = today_response.data['data']
        self.assertEqual(today_data['reminders_summary'], {'total': 3, 'active': 1, 'inactive': 2})
        today_counts = {
            item['medicine_type']: item['count']
            for item in today_data['medicine_summary']['items']
        }
        self.assertEqual(today_counts['tablet'], 1)
        self.assertEqual(today_counts['capsule'], 0)
        self.assertEqual(today_counts['syrup'], 0)

        future_response = self.client.get('/api/dashboard/?date=2026-03-23')
        self.assertEqual(future_response.status_code, 200)
        future_data = future_response.data['data']
        self.assertEqual(future_data['reminders_summary'], {'total': 3, 'active': 2, 'inactive': 1})
        future_counts = {
            item['medicine_type']: item['count']
            for item in future_data['medicine_summary']['items']
        }
        self.assertEqual(future_counts['tablet'], 1)
        self.assertEqual(future_counts['capsule'], 1)
        self.assertEqual(future_counts['syrup'], 0)
