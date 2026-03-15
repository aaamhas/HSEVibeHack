from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from backend.database import Base

# Association table for many-to-many relationship between Hackathon and Technology
hackathon_technology = Table(
    "hackathon_technology",
    Base.metadata,
    Column("hackathon_id", Integer, ForeignKey("hackathons.id"), primary_key=True),
    Column("technology_id", Integer, ForeignKey("technologies.id"), primary_key=True),
)


class Technology(Base):
    __tablename__ = "technologies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, nullable=True)  # e.g., "Language", "Framework", "Tool"
    created_at = Column(DateTime, default=datetime.utcnow)

    hackathons = relationship(
        "Hackathon",
        secondary=hackathon_technology,
        back_populates="technologies",
    )


class Hackathon(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)
    format = Column(String, default="online")  # "online", "offline", "hybrid"
    url = Column(String, nullable=True)
    location = Column(String, nullable=True)  # City/venue
    source = Column(String, nullable=True)  # e.g., "devpost", "hackerearth"
    theme = Column(String, nullable=True)  # e.g., "fintech", "ai", "gamedev"
    skill_level = Column(String, nullable=True)  # "beginner", "intermediate", "advanced", "any"
    team_size_min = Column(Integer, nullable=True)
    team_size_max = Column(Integer, nullable=True)
    prize = Column(String, nullable=True)  # Prize description
    duration_hours = Column(Integer, nullable=True)  # Duration in hours
    created_at = Column(DateTime, default=datetime.utcnow)

    technologies = relationship(
        "Technology",
        secondary=hackathon_technology,
        back_populates="hackathons",
    )


from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from backend.database import Base

# Association table for many-to-many relationship between Hackathon and Technology
hackathon_technology = Table(
    "hackathon_technology",
    Base.metadata,
    Column("hackathon_id", Integer, ForeignKey("hackathons.id"), primary_key=True),
    Column("technology_id", Integer, ForeignKey("technologies.id"), primary_key=True),
)


class Technology(Base):
    __tablename__ = "technologies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String, nullable=True)  # e.g., "Language", "Framework", "Tool"
    created_at = Column(DateTime, default=datetime.utcnow)

    hackathons = relationship(
        "Hackathon",
        secondary=hackathon_technology,
        back_populates="technologies",
    )


class Hackathon(Base):
    __tablename__ = "hackathons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    registration_deadline = Column(DateTime, nullable=True)
    format = Column(String, default="online")  # "online" or "offline"
    url = Column(String, nullable=True)
    location = Column(String, nullable=True)  # City/venue
    source = Column(String, nullable=True)  # e.g., "devpost", "hackerearth"
    created_at = Column(DateTime, default=datetime.utcnow)

    technologies = relationship(
        "Technology",
        secondary=hackathon_technology,
        back_populates="hackathons",
    )
    user_hackathons = relationship("UserHackathon", back_populates="hackathon", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_hackathons = relationship("UserHackathon", back_populates="user", cascade="all, delete-orphan")


class UserHackathon(Base):
    __tablename__ = "user_hackathons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    hackathon_id = Column(Integer, ForeignKey("hackathons.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="user_hackathons")
    hackathon = relationship("Hackathon", back_populates="user_hackathons")

