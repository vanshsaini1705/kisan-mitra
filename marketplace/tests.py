from datetime import date, timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from .models import User, Product


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class UserModelTest(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='test_farmer', password='pass1234', role=User.FARMER,
        )
        self.buyer = User.objects.create_user(
            username='test_buyer', password='pass1234', role=User.BUYER,
        )

    def test_is_farmer(self):
        self.assertTrue(self.farmer.is_farmer())
        self.assertFalse(self.farmer.is_buyer())

    def test_is_buyer(self):
        self.assertTrue(self.buyer.is_buyer())
        self.assertFalse(self.buyer.is_farmer())

    def test_str(self):
        self.assertIn('test_farmer', str(self.farmer))


class ProductModelTest(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer1', password='pass1234', role=User.FARMER,
        )

    def _make_product(self, crop_name='tomato', days_ago=0):
        harvest = date.today() - timedelta(days=days_ago)
        return Product.objects.create(
            farmer=self.farmer,
            crop_name=crop_name,
            quantity=100,
            price=20,
            location='Jaipur',
            harvest_date=harvest,
        )

    def test_expiry_auto_calculated_for_tomato(self):
        p = self._make_product('tomato')
        expected = date.today() + timedelta(days=5)   # shelf life = 5 days
        self.assertEqual(p.expiry_date, expected)

    def test_expiry_default_for_unknown_crop(self):
        p = self._make_product('exotic_berry')
        expected = date.today() + timedelta(days=Product.DEFAULT_SHELF_DAYS)
        self.assertEqual(p.expiry_date, expected)

    def test_urgency_fresh(self):
        p = self._make_product('rice')   # shelf life 365 days
        self.assertEqual(p.urgency_level, 'fresh')

    def test_urgency_expired(self):
        p = self._make_product('tomato', days_ago=10)  # harvested 10 days ago, expires after 5
        self.assertEqual(p.urgency_level, 'expired')

    def test_crop_emoji_tomato(self):
        p = self._make_product('tomato')
        self.assertEqual(p.crop_emoji, '🍅')

    def test_crop_emoji_unknown(self):
        p = self._make_product('mystery_veg')
        self.assertEqual(p.crop_emoji, '🌿')

    def test_str_representation(self):
        p = self._make_product('wheat')
        self.assertIn('wheat', str(p).lower())


# ---------------------------------------------------------------------------
# View tests
# ---------------------------------------------------------------------------

class HomeViewTest(TestCase):
    def test_home_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_home_search(self):
        response = self.client.get(reverse('home'), {'q': 'tomato'})
        self.assertEqual(response.status_code, 200)


class AuthViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser', password='testpass123', role=User.BUYER,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_login_correct_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'authuser',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_wrong_password(self):
        response = self.client.post(reverse('login'), {
            'username': 'authuser',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)


class FarmerDashboardTest(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='dashfarmer', password='pass1234', role=User.FARMER,
        )
        self.buyer = User.objects.create_user(
            username='dashbuyer', password='pass1234', role=User.BUYER,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('farmer_dashboard'))
        self.assertRedirects(response, f'/login/?next=/farmer/dashboard/')

    def test_farmer_can_access_dashboard(self):
        self.client.login(username='dashfarmer', password='pass1234')
        response = self.client.get(reverse('farmer_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_buyer_cannot_access_dashboard(self):
        self.client.login(username='dashbuyer', password='pass1234')
        response = self.client.get(reverse('farmer_dashboard'))
        self.assertRedirects(response, reverse('home'))


class KisanMitraChatTest(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='chatfarmer', password='pass1234', role=User.FARMER,
        )
        self.client.login(username='chatfarmer', password='pass1234')

    def test_empty_message_rejected(self):
        import json
        response = self.client.post(
            reverse('kisan_mitra_chat'),
            data=json.dumps({'message': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_json_rejected(self):
        response = self.client.post(
            reverse('kisan_mitra_chat'),
            data='not json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)