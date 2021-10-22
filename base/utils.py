from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.core.cache import cache
import time
from django.db import connection
from taicat.models import Image
import pandas as pd


class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)


generate_token = TokenGenerator()
