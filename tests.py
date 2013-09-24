import json
from django.test import TestCase
from django.contrib.auth.models import User


def setUp():
    User.objects.create_user(
        first_name='brett', email='theiviaxx@gmail.com', password='top_secret')

class FrogTestCase(TestCase):
    fixtures = ['test_data.json']

    def test_filter(self):
        res = self.client.get('/frog/gallery/1/filter')
        data = json.loads(res.content)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['isSuccess'], True)

        res = self.client.get('/frog/gallery/1#{"filters":[[100000000]]}')
        self.assertEqual(res.status_code, 200)

    def test_get(self):
        res = self.client.get('/frog/gallery/1')
        self.assertEqual(res.status_code, 200)

    def test_create_gallery(self):
        res = self.client.post('/frog/gallery', {'title': 'test_gallery'})
        print res.content
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/frog/gallery')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/frog/gallery')
        data = json.loads(res.content)
        self.assertEqual(len(data['values']), 3)