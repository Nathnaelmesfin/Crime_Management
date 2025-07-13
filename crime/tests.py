from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import TemporaryDetention, DetaineeItem


class DetaineeItemTestCase(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="officer",
            email="officer@example.com",
            password="pass",
            user_type="front_line_officer",
        )

    def test_route_set_automatically(self):
        detention = TemporaryDetention.objects.create(
            detainee_name="John Doe",
            created_by=self.user,
        )
        item = DetaineeItem.objects.create(
            detention=detention,
            description="Knife",
            suspected_link=True,
            logged_by=self.user,
        )
        self.assertEqual(item.route, "EXHIBIT")

        item2 = DetaineeItem.objects.create(
            detention=detention,
            description="Wallet",
            suspected_link=False,
            logged_by=self.user,
        )
        self.assertEqual(item2.route, "STORE")
