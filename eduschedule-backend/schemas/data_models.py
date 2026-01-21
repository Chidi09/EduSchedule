from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from uuid import UUID
import re
import html

# --- 1. THE SANITIZER CORE ---
class SafeBaseModel(BaseModel):
    """
    A base model that sanitizes all string fields to prevent XSS
    and strips leading/trailing whitespace.
    """
    @model_validator(mode='before')
    @classmethod
    def sanitize_strings(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    # 1. Strip whitespace
                    value = value.strip()
                    # 2. Basic XSS prevention (strip HTML tags)
                    # This removes <script> tags and other HTML
                    clean_value = re.sub('<[^<]+?>', '', value)
                    # 3. Unescape entities (optional, keeps text readable)
                    new_data[key] = html.unescape(clean_value)
                else:
                    new_data[key] = value
            return new_data
        return data

# --- 2. ENHANCED USER MODELS ---
class UserCreate(SafeBaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    password: str = Field(..., min_length=8, description="Must be at least 8 chars")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        return v

class UserLogin(SafeBaseModel):
    email: EmailStr
    password: str

# --- 3. ENHANCED DATA MODELS ---
class TeacherBase(SafeBaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr

    # "qualifications" is a list of strings, we validate each item
    subjects: List[str] = Field(default_factory=list)

class TeacherCreate(TeacherBase):
    preferences: Optional[Dict] = {}

# Base schemas (for reading from API)
class TeacherRead(SafeBaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: EmailStr
    subjects: List[str]
    availability: Optional[Any] = None
    preferences: Optional[Any] = None

class RoomBase(SafeBaseModel):
    id: UUID
    name: str
    capacity: int
    features: Optional[Any] = None

class RoomCreate(SafeBaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    capacity: int = Field(..., gt=0, le=1000)
    features: Optional[List[str]] = Field(default_factory=list)

class SubjectBase(SafeBaseModel):
    id: UUID
    name: str
    required_features: Optional[Any] = None
    periods_per_week: int

class SubjectCreate(SafeBaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    periods_per_week: int = Field(..., gt=0, le=20)
    required_features: Optional[List[str]] = Field(default_factory=list)

class ClassBase(SafeBaseModel):
    id: UUID
    name: str
    student_count: int
    grade_level: Optional[int] = None

class ClassCreate(SafeBaseModel):
    name: str = Field(..., pattern=r"^[A-Za-z0-9\s\-\.]+$", description="Alphanumeric, spaces, dashes only")
    student_count: int = Field(..., gt=0, le=500)
    grade_level: int = Field(..., ge=1, le=12)
