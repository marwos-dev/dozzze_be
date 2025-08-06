import os

DEVELOPMENT = os.getenv("DJANGO_ENV", "development") == "development"

if DEVELOPMENT:
    from .development import *  # noqa: F401,F403
else:
    from .production import *  # noqa: F401,F403
