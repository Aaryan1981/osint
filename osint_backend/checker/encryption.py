import base64
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

class EncryptedCharField(models.CharField):
    """
    A custom CharField that encrypts data before saving to the database
    and decrypts it when retrieving, using the Django SECRET_KEY.
    """
    def __init__(self, *args, **kwargs):
        # Ensure max_length is large enough for base64 encrypted payload
        if 'max_length' in kwargs:
            kwargs['max_length'] = max(kwargs['max_length'], 500)
        super().__init__(*args, **kwargs)

    def get_fernet(self):
        # Create a valid 32-byte url-safe base64 key from Django's SECRET_KEY
        key = settings.SECRET_KEY[:32].ljust(32, 'x').encode('utf-8')
        return Fernet(base64.urlsafe_b64encode(key))

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value:
            return value
        # Encrypt the string
        return self.get_fernet().encrypt(value.encode('utf-8')).decode('utf-8')

    def from_db_value(self, value, expression, connection):
        if not value:
            return value
        try:
            return self.get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')
        except Exception:
            # If decryption fails (e.g. legacy plain text data), return it as is
            return value

    def to_python(self, value):
        if isinstance(value, str):
            try:
                # Try to decrypt in case it's passed as an encrypted string
                return self.get_fernet().decrypt(value.encode('utf-8')).decode('utf-8')
            except Exception:
                pass
        return super().to_python(value)
