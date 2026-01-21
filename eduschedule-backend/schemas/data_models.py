# schemas/data_models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from uuid import UUID

# Base schemas (for reading from API)
class TeacherBase(BaseModel):
    id: UUID
    user_id: UUID
    availability: Optional[Any] = None
    preferences: Optional[Any] = None

class RoomBase(BaseModel):
    id: UUID
    name: str
    capacity: int
    features: Optional[Any] = None

class SubjectBase(BaseModel):
    id: UUID
    name: str
    required_features: Optional[Any] = None
    periods_per_week: int

class ClassBase(BaseModel):
    id: UUID
    name: str
    student_count: int

# Create schemas (for writing to API)
class TeacherCreate(BaseModel):
    user_id: UUID # We'll need to link this to a user
    availability: Optional[Any] = {}
    preferences: Optional[Any] = {}

class RoomCreate(BaseModel):
    name: str
    capacity: int
    features: Optional[Any] = []

class SubjectCreate(BaseModel):
    name: str
    required_features: Optional[Any] = []
    periods_per_week: int

class ClassCreate(BaseModel):
    name: str
    student_count: int