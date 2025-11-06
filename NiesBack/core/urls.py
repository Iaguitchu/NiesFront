from fastapi import Request
from urllib.parse import urlencode

def build_verify_link(request: Request, token: str) -> str:
    # pode também apontar para FRONT_BASE_URL + rota do front
    base = str(request.base_url).rstrip("/")
    query = urlencode({"token": token})
    return f"{base}/auth/verify?{query}"
