from pydantic import BaseModel, EmailStr, Field


class OTPVerification(BaseModel):
    email: EmailStr
    otp: str


class OTPResponse(BaseModel):
    message: str

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str = Field(
        min_length=6,
        max_length=6,
    )

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class AdminResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class PasswordSetupRequest(BaseModel):
    token: str
    password: str = Field(
        min_length=8,
        max_length=128,
    )

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str

    password: str = Field(
        min_length=8,
        max_length=128,
    )