import hashlib

from django.utils.crypto import get_random_string


def get_random_hash(length=32):
    return hashlib.sha1(get_random_string().encode("utf8")).hexdigest()[:length]
