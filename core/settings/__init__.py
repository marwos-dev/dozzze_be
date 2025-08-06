import os

env = os.getenv("DJANGO_ENV", "development")

if env == "production":
    from .production import *  # noqa: F401,F403
else:
    from .development import *  # noqa: F401,F403
