from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .settings import settings

def _serializer() -> URLSafeTimedSerializer:
    # settings.SECRET_KEY e settings.INVITE_SALT precisam existir
    return URLSafeTimedSerializer(secret_key=settings.SECRET_KEY, salt=settings.INVITE_SALT)

def make_invite_token(payload: dict) -> str:
    # payload: { "email": ..., "name": ..., "cpf": ..., "phone": ..., "valid_from": "YYYY-MM-DD"|None, "valid_to": "YYYY-MM-DD"|None, "group_ids": [...] }
    return _serializer().dumps(payload)

# Verifica expiração usando max_age (em segundos). Se passou, levanta SignatureExpired.
def read_invite_token(token: str, max_age_seconds: int) -> dict:
    s = _serializer()
    try:
        return s.loads(token, max_age=max_age_seconds)
    except SignatureExpired as e:
        # expirou
        raise
    except BadSignature as e:
        # token inválido
        raise
