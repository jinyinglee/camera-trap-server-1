from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from django.core.cache import cache
import time
from django.db import connection
from taicat.models import Image
import pandas as pd
import json
from decimal import Decimal


class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
