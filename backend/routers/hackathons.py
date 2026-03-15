from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from backend.database import get_db
from backend.models import Hackathon, Technology
from backend.schemas import (
    HackathonResponse,
    HackathonCreate,
    TechnologyResponse,
    TechnologyCreate,
    AISearchResponse,
)
from backend.ai_recommender import AIRecommender

router = APIRouter(prefix="/hackathons", tags=["hackathons"])
ai_recommender = AIRecommender()


@router.get("", response_model=List[HackathonResponse])
async def list_hackathons(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all hackathons with pagination"""
    hackathons = db.query(Hackathon).offset(skip).limit(limit).all()
    return hackathons


@router.get("/{hackathon_id}", response_model=HackathonResponse)
async def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)):
    """Get a specific hackathon by ID"""
    hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return hackathon


@router.post("", response_model=HackathonResponse)
async def create_hackathon(hackathon: HackathonCreate, db: Session = Depends(get_db)):
    """Create a new hackathon"""
    technology_ids = hackathon.technology_ids or []

    db_hackathon = Hackathon(
        title=hackathon.title,
        description=hackathon.description,
        start_date=hackathon.start_date,
        end_date=hackathon.end_date,
        registration_deadline=hackathon.registration_deadline,
        format=hackathon.format,
        url=hackathon.url,
        location=hackathon.location,
        source=hackathon.source,
        theme=hackathon.theme,
        skill_level=hackathon.skill_level,
        team_size_min=hackathon.team_size_min,
        team_size_max=hackathon.team_size_max,
        prize=hackathon.prize,
        duration_hours=hackathon.duration_hours,
    )

    # Add technologies
    if technology_ids:
        technologies = db.query(Technology).filter(Technology.id.in_(technology_ids)).all()
        db_hackathon.technologies.extend(technologies)

    db.add(db_hackathon)
    db.commit()
    db.refresh(db_hackathon)
    return db_hackathon


@router.put("/{hackathon_id}", response_model=HackathonResponse)
async def update_hackathon(
    hackathon_id: int, hackathon: HackathonCreate, db: Session = Depends(get_db)
):
    """Update an existing hackathon"""
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    db_hackathon.title = hackathon.title
    db_hackathon.description = hackathon.description
    db_hackathon.start_date = hackathon.start_date
    db_hackathon.end_date = hackathon.end_date
    db_hackathon.registration_deadline = hackathon.registration_deadline
    db_hackathon.format = hackathon.format
    db_hackathon.url = hackathon.url
    db_hackathon.location = hackathon.location
    db_hackathon.source = hackathon.source
    db_hackathon.theme = hackathon.theme
    db_hackathon.skill_level = hackathon.skill_level
    db_hackathon.team_size_min = hackathon.team_size_min
    db_hackathon.team_size_max = hackathon.team_size_max
    db_hackathon.prize = hackathon.prize
    db_hackathon.duration_hours = hackathon.duration_hours

    # Update technologies
    if hackathon.technology_ids is not None:
        technologies = db.query(Technology).filter(Technology.id.in_(hackathon.technology_ids)).all()
        db_hackathon.technologies = technologies

    db.commit()
    db.refresh(db_hackathon)
    return db_hackathon


@router.delete("/{hackathon_id}")
async def delete_hackathon(hackathon_id: int, db: Session = Depends(get_db)):
    """Delete a hackathon"""
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    db.delete(db_hackathon)
    db.commit()
    return {"message": "Hackathon deleted"}


@router.get("/search/query", response_model=List[HackathonResponse])
async def search_hackathons(
    q: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search hackathons by title or description (basic text search)"""
    hackathons = (
        db.query(Hackathon)
        .filter(
            (Hackathon.title.ilike(f"%{q}%")) | (Hackathon.description.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    return hackathons


@router.get("/search/ai", response_model=AISearchResponse)
async def search_hackathons_ai(
    q: str = Query(..., description="Search query in natural language"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search hackathons using AI-powered semantic search with structured query parsing.

    Extracts from user query: technologies, dates, format, location,
    skill level, theme, team size, prize, duration, and other details.
    """
    now = datetime.utcnow()
    all_hackathons = (
        db.query(Hackathon)
        .filter(
            (Hackathon.registration_deadline > now)
            | (Hackathon.registration_deadline.is_(None))
        )
        .all()
    )

    hackathons_dict = [
        {
            "id": h.id,
            "title": h.title,
            "description": h.description or "",
            "start_date": h.start_date,
            "end_date": h.end_date,
            "registration_deadline": h.registration_deadline,
            "format": h.format,
            "url": h.url,
            "location": h.location,
            "source": h.source,
            "theme": h.theme,
            "skill_level": h.skill_level,
            "team_size_min": h.team_size_min,
            "team_size_max": h.team_size_max,
            "prize": h.prize,
            "duration_hours": h.duration_hours,
            "technologies": [t.name for t in h.technologies],
            "created_at": h.created_at,
        }
        for h in all_hackathons
    ]

    ranked_hackathons, parsed_query, follow_up_questions = ai_recommender.rank_hackathons(
        q, hackathons_dict, limit
    )

    return AISearchResponse(
        hackathons=[HackathonResponse(**h) for h in ranked_hackathons],
        parsed_query=parsed_query,
        follow_up_questions=follow_up_questions,
    )


# Technologies endpoints
@router.get("/technologies", response_model=List[TechnologyResponse])
async def list_technologies(db: Session = Depends(get_db)):
    """List all available technologies"""
    technologies = db.query(Technology).all()
    return technologies


@router.post("/technologies", response_model=TechnologyResponse)
async def create_technology(
    technology: TechnologyCreate, db: Session = Depends(get_db)
):
    """Create a new technology"""
    existing = db.query(Technology).filter(Technology.name == technology.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Technology already exists")

    db_technology = Technology(**technology.dict())
    db.add(db_technology)
    db.commit()
    db.refresh(db_technology)
    return db_technology


@router.delete("/technologies/{tech_id}")
async def delete_technology(tech_id: int, db: Session = Depends(get_db)):
    """Delete a technology"""
    db_technology = db.query(Technology).filter(Technology.id == tech_id).first()
    if not db_technology:
        raise HTTPException(status_code=404, detail="Technology not found")

    db.delete(db_technology)
    db.commit()
    return {"message": "Technology deleted"}

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from backend.database import get_db
from backend.models import Hackathon, Technology
from backend.schemas import (
    HackathonResponse,
    HackathonCreate,
    TechnologyResponse,
    TechnologyCreate,
)
from backend.ai_recommender import AIRecommender
from backend.hackathon_service import HackathonService
from backend.config.logging_config import get_logger

logger = get_logger(__name__)
hackathon_service = HackathonService()

router = APIRouter(prefix="/hackathons", tags=["hackathons"])
ai_recommender = AIRecommender()


@router.get("", response_model=List[HackathonResponse])
async def list_hackathons(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all hackathons with pagination"""
    hackathons = db.query(Hackathon).offset(skip).limit(limit).all()
    return hackathons


@router.get("/{hackathon_id}", response_model=HackathonResponse)
async def get_hackathon(hackathon_id: int, db: Session = Depends(get_db)):
    """Get a specific hackathon by ID"""
    hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")
    return hackathon


@router.post("", response_model=HackathonResponse)
async def create_hackathon(hackathon: HackathonCreate, db: Session = Depends(get_db)):
    """Create a new hackathon"""
    try:
        technology_ids = hackathon.technology_ids or []

        db_hackathon = Hackathon(
            title=hackathon.title,
            description=hackathon.description,
            start_date=hackathon.start_date,
            end_date=hackathon.end_date,
            registration_deadline=hackathon.registration_deadline,
            format=hackathon.format,
            url=hackathon.url,
            location=hackathon.location,
            source=hackathon.source,
        )

        # Add technologies
        if technology_ids:
            technologies = db.query(Technology).filter(Technology.id.in_(technology_ids)).all()
            db_hackathon.technologies.extend(technologies)

        db.add(db_hackathon)
        db.commit()
        db.refresh(db_hackathon)
        logger.info(f"Created hackathon: {db_hackathon.title} (ID: {db_hackathon.id})")
        return db_hackathon
    except Exception as e:
        logger.error(f"Error creating hackathon: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating hackathon")


@router.put("/{hackathon_id}", response_model=HackathonResponse)
async def update_hackathon(
    hackathon_id: int, hackathon: HackathonCreate, db: Session = Depends(get_db)
):
    """Update an existing hackathon"""
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    db_hackathon.title = hackathon.title
    db_hackathon.description = hackathon.description
    db_hackathon.start_date = hackathon.start_date
    db_hackathon.end_date = hackathon.end_date
    db_hackathon.registration_deadline = hackathon.registration_deadline
    db_hackathon.format = hackathon.format
    db_hackathon.url = hackathon.url
    db_hackathon.location = hackathon.location
    db_hackathon.source = hackathon.source

    # Update technologies
    if hackathon.technology_ids is not None:
        technologies = db.query(Technology).filter(Technology.id.in_(hackathon.technology_ids)).all()
        db_hackathon.technologies = technologies

    db.commit()
    db.refresh(db_hackathon)
    return db_hackathon


@router.delete("/{hackathon_id}")
async def delete_hackathon(hackathon_id: int, db: Session = Depends(get_db)):
    """Delete a hackathon"""
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    db.delete(db_hackathon)
    db.commit()
    return {"message": "Hackathon deleted"}


@router.get("/search/query", response_model=List[HackathonResponse])
async def search_hackathons(
    q: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search hackathons by title or description (basic text search)"""
    hackathons = (
        db.query(Hackathon)
        .filter(
            (Hackathon.title.ilike(f"%{q}%")) | (Hackathon.description.ilike(f"%{q}%"))
        )
        .limit(limit)
        .all()
    )
    return hackathons


@router.get("/search/ai", response_model=List[HackathonResponse])
async def search_hackathons_ai(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Search hackathons using AI-powered semantic search with Qwen2"""
    try:
        logger.info(f"AI search initiated with query: '{q}'")
        now = datetime.utcnow()
        all_hackathons = (
            db.query(Hackathon)
            .filter(Hackathon.registration_deadline > now)
            .all()
        )

        hackathons_dict = [
            {
                "id": h.id,
                "title": h.title,
                "description": h.description or "",
                "start_date": h.start_date,
                "end_date": h.end_date,
                "registration_deadline": h.registration_deadline,
                "format": h.format,
                "url": h.url,
                "location": h.location,
                "source": h.source,
                "technologies": [t.name for t in h.technologies],
                "created_at": h.created_at,
            }
            for h in all_hackathons
        ]

        ranked_hackathons = ai_recommender.rank_hackathons(q, hackathons_dict, limit)
        logger.info(f"AI search returned {len(ranked_hackathons)} results for query: '{q}'")
        return [HackathonResponse(**h) for h in ranked_hackathons]
    except Exception as e:
        logger.error(f"Error in AI search for query '{q}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error performing AI search")


# Technologies endpoints
@router.get("/technologies", response_model=List[TechnologyResponse])
async def list_technologies(db: Session = Depends(get_db)):
    """List all available technologies"""
    technologies = db.query(Technology).all()
    return technologies


@router.post("/technologies", response_model=TechnologyResponse)
async def create_technology(
    technology: TechnologyCreate, db: Session = Depends(get_db)
):
    """Create a new technology"""
    existing = db.query(Technology).filter(Technology.name == technology.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Technology already exists")

    db_technology = Technology(**technology.dict())
    db.add(db_technology)
    db.commit()
    db.refresh(db_technology)
    return db_technology


@router.delete("/technologies/{tech_id}")
async def delete_technology(tech_id: int, db: Session = Depends(get_db)):
    """Delete a technology"""
    db_technology = db.query(Technology).filter(Technology.id == tech_id).first()
    if not db_technology:
        raise HTTPException(status_code=404, detail="Technology not found")

    db.delete(db_technology)
    db.commit()
    return {"message": "Technology deleted"}


# Parser endpoints
@router.post("/parse/update")
async def run_parser_update(db: Session = Depends(get_db)):
    """
    Trigger hackathon parsing from all sources.
    This endpoint runs all configured parsers and adds new hackathons to the database.
    """
    try:
        logger.info("Parser update triggered via API")
        summary = await hackathon_service.run_all_parsers(db)
        logger.info(f"Parser update completed: {summary}")
        return summary
    except Exception as e:
        logger.error(f"Error during parser update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error running parsers")


@router.get("/parse/sources")
async def get_parser_sources():
    """Get list of available parser sources"""
    try:
        sources = hackathon_service.get_parser_sources()
        logger.info(f"Parser sources requested: {sources}")
        return {"sources": sources}
    except Exception as e:
        logger.error(f"Error getting parser sources: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error getting parser sources")
