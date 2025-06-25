from django.core import signing


def generate_activation_token(user_id: int) -> str:
    return signing.dumps(user_id, salt="account-activation")


def verify_activation_token(token: str, max_age_seconds: int = 86400) -> int:
    return signing.loads(token, salt="account-activation", max_age=max_age_seconds)
