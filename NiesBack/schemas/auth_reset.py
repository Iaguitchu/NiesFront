from pydantic import BaseModel, EmailStr, StringConstraints
from typing_extensions import Annotated

SixDigits = Annotated[str, StringConstraints(min_length=6, max_length=6, pattern=r"^\d{6}$")]

class ForgotVerifyIn(BaseModel):
    email: EmailStr
    code: SixDigits

class ResetPasswordIn(BaseModel):
    email: EmailStr
    code: SixDigits
    new_password: Annotated[str, StringConstraints(min_length=6)]
    reset_token: str