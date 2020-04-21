from django.test import TestCase, Client

class CommonTest(TestCase):
    def setUp(self):
        self.client = Client()
    def test_404(self):
        response = self.client.get("/this/page/does/not/exist/for/sure/")
        self.assertEqual(response.status_code, 404, "404 status code is expected when the page is not found")
