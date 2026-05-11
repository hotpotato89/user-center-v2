from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr, field_validator

class ReturnForm(BaseModel): #Универсальный
    success: bool
    message: str
    error_code: Optional[str] = None
    data: Optional[Any] = None
    total: Optional[int] = None
    page: Optional[int] = None
    total_pages: Optional[int] = None
    limit: Optional[int] = None

class PasswordForm(BaseModel):
    password: str = Field(..., min_length=1, max_length=128, description='Пароль для выполнения команды')

    @field_validator('password')
    @classmethod
    def password_strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Пароль не должен быть пустым')
        return v
        
class UserIdForm(BaseModel):
    id: int = Field(..., ge=1, description='id пользователя')

class UserDataForm(BaseModel):
    name: str = Field(..., min_length=1,  max_length=60, description='Имя пользователя')
    age: int = Field(..., ge=1, le=120, description='Возраст пользователя')
    email: EmailStr = Field(..., max_length=45, description='Email пользователя')

    @field_validator('email')
    @classmethod
    def email_lower(cls, v: str) -> str:
        return v.lower()
    
class DeleteUserForm(BaseModel):
    id: int = Field(..., ge=1, description='id пользователя')
    password: str = Field(..., min_length=1, max_length=123, description='Админ-пароль')

    @field_validator('password')
    @classmethod
    def password_strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Пароль не должен быть пустым')
        return v