from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Hackathon, UserHackathon
from backend.schemas import AddToCalendarRequest, AddToCalendarResponse
from backend.services.google_calendar import add_hackathon_to_calendar
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/add-hackathon", response_model=AddToCalendarResponse)
async def add_hackathon_to_calendar_endpoint(
    request: AddToCalendarRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a hackathon to user's Google Calendar

    Requires: Authorization: Bearer JWT_ACCESS_TOKEN
    """
    hackathon = db.query(Hackathon).filter(Hackathon.id == request.hackathon_id).first()

    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="User has not connected Google Calendar. Please re-authenticate.")

    # Add event to user's Google Calendar using their Google access token
    result = add_hackathon_to_calendar(
        current_user.access_token,
        title=hackathon.title,
        start_date=hackathon.start_date,
        end_date=hackathon.end_date,
        description=hackathon.description,
        location=hackathon.location,
    )

    if result["success"]:
        # Save to database that user added this hackathon to calendar
        user_hackathon = UserHackathon(
            user_id=current_user.id,
            hackathon_id=hackathon.id,
            calendar_event_id=result.get("event_id"),
            added_to_calendar=db.func.now(),
        )
        db.add(user_hackathon)
        db.commit()

        return AddToCalendarResponse(
            success=True,
            message="Hackathon added to your Google Calendar",
            event_id=result.get("event_id"),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Failed to add to calendar: {result.get('error')}")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Hackathon, UserHackathon
from backend.schemas import AddToCalendarRequest, AddToCalendarResponse
from backend.services.google_calendar import add_hackathon_to_calendar
from backend.routers.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.post("/add-hackathon", response_model=AddToCalendarResponse)
async def add_hackathon_to_calendar_endpoint(
    request: AddToCalendarRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a hackathon to user's Google Calendar

    Requires: Authorization: Bearer JWT_ACCESS_TOKEN
    """
    hackathon = db.query(Hackathon).filter(Hackathon.id == request.hackathon_id).first()

    if not hackathon:
        raise HTTPException(status_code=404, detail="Hackathon not found")

    if not current_user.access_token:
        raise HTTPException(status_code=400, detail="User has not connected Google Calendar. Please re-authenticate.")

    # Add event to user's Google Calendar using their Google access token
    result = add_hackathon_to_calendar(
        current_user.access_token,
        title=hackathon.title,
        start_date=hackathon.start_date,
        end_date=hackathon.end_date,
        description=hackathon.description,
        location=hackathon.location,
    )

    if result["success"]:
        # Save to database that user added this hackathon to calendar
        user_hackathon = UserHackathon(
            user_id=current_user.id,
            hackathon_id=hackathon.id,
            calendar_event_id=result.get("event_id"),
            added_to_calendar=db.func.now(),
        )
        db.add(user_hackathon)
        db.commit()

        return AddToCalendarResponse(
            success=True,
            message="Hackathon added to your Google Calendar",
            event_id=result.get("event_id"),
        )
    else:
        raise HTTPException(status_code=400, detail=f"Failed to add to calendar: {result.get('error')}")

