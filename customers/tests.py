from django.test import TestCase
from utils.tokens import generate_activation_token, verify_activation_token


class TokensTest(TestCase):
    def test_token_roundtrip(self):
        token = generate_activation_token(1)
        self.assertEqual(verify_activation_token(token), 1)

