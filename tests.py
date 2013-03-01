
from django.test import TestCase
from django.conf import settings


class FilterTestCase(TestCase):
    fixtures = ['test_data.json']
    def filterAll(self):
        
        res = self.client.get(settings.LOGIN_URL + '/gallery/1/filter')
        self.assertEqual(res.status_code, 200)
