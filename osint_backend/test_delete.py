import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "osint_backend.settings")
django.setup()

from checker.models import User

try:
    user = User.objects.last()
    if user:
        print(f"Deleting {user.email}...")
        user.delete()
        print("Success")
    else:
        print("No users found")
except Exception as e:
    import traceback
    traceback.print_exc()
