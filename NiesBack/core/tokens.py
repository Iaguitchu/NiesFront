from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from core.settings import SECRET, SALT_EMAIL_VERIFY

EXPIRES_SECONDS = 3600 * 24  # 24h

def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=SECRET, salt=SALT_EMAIL_VERIFY)

def make_email_token(user_id: str) -> str:
    return _serializer().dumps({"uid": user_id})

def read_email_token(token: str) -> dict:
    return _serializer().loads(token, max_age=EXPIRES_SECONDS)
