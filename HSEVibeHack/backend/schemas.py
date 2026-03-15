from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    google_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class TechnologyResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True


class TechnologyCreate(BaseModel):
    name: str
    category: Optional[str] = None


class HackathonResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    format: str = "online"
    url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    theme: Optional[str] = None
    skill_level: Optional[str] = None
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    prize: Optional[str] = None
    duration_hours: Optional[int] = None
    technologies: List[TechnologyResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class HackathonCreate(BaseModel):
    title: str
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    format: str = "online"
    url: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None
    theme: Optional[str] = None
    skill_level: Optional[str] = None
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    prize: Optional[str] = None
    duration_hours: Optional[int] = None
    technology_ids: Optional[List[int]] = []


class HackathonSearch(BaseModel):
    query: str
    limit: int = 10


class AISearchResponse(BaseModel):
    hackathons: List[HackathonResponse] = []
    parsed_query: dict = {}
    follow_up_questions: List[str] = []


class AddToCalendarRequest(BaseModel):
    hackathon_id: int


class AddToCalendarResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[str] = None

