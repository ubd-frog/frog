
from django.test import TestCase


class FilterTestCase(TestCase):
    fixtures = ['test_data.json']
    def filterAll(self):
        
        res = self.client.get('/frog/gallery/1/filter')
        self.assertEqual(res.status_code, 200)
