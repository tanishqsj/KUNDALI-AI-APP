"""
Kundali Milan (Matching) API Routes

Enhanced to accept full birth details and persist matching results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from typing import List, Optional
from datetime import date, time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_current_user
from app.persistence.db import get_db_session
from app.persistence.models.birth_profile import BirthProfile
from app.persistence.models.kundali_core import KundaliCore
from app.persistence.models.kundali_derived import KundaliDerived
from app.persistence.repositories.kundali_match_repo import KundaliMatchRepository
from app.services.kundali_service import KundaliService
from app.services.matching_service import MatchingService
from app.services.matching_report_service import MatchingReportService


router = APIRouter()


# ─────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────

class PersonDetails(BaseModel):
    """Birth details for one person."""
    name: str = Field(..., example="Rahul Sharma")
    birth_date: str = Field(..., example="1995-05-15")
    birth_time: str = Field(..., example="10:30")
    birth_place: str = Field(..., example="Mumbai, Maharashtra, India")
    latitude: float = Field(..., example=19.0760)
    longitude: float = Field(..., example=72.8777)
    timezone: str = Field(..., example="Asia/Kolkata")


class MatchRequest(BaseModel):
    """Request with full birth details for both partners."""
    boy: PersonDetails
    girl: PersonDetails


class MatchFactor(BaseModel):
    name: str
    score: float
    max: int
    description: str
    boy_value: Optional[str] = None
    girl_value: Optional[str] = None
    area: Optional[str] = None


class MatchResponse(BaseModel):
    match_id: UUID
    boy_kundali_id: UUID
    girl_kundali_id: UUID
    total_score: float
    max_score: int
    percentage: float
    verdict: str
    factors: List[MatchFactor]
    boy_name: str
    girl_name: str


# ─────────────────────────────────────────────
# Helper: Find or Create Kundali
# ─────────────────────────────────────────────

async def find_or_create_kundali(
    session: AsyncSession,
    user_id: UUID,
    details: PersonDetails,
) -> tuple[UUID, dict]:
    """
    Check if kundali exists for the given birth details.
    If yes, return existing kundali_core_id.
    If no, create new kundali and return its ID.
    """
    birth_date_obj = date.fromisoformat(details.birth_date)
    birth_time_obj = time.fromisoformat(details.birth_time)

    # Search for existing birth profile
    result = await session.execute(
        select(BirthProfile).where(
            BirthProfile.name == details.name,
            BirthProfile.birth_date == birth_date_obj,
            BirthProfile.birth_time == birth_time_obj,
            BirthProfile.birth_place == details.birth_place,
        )
    )
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        # Find associated kundali_core
        core_result = await session.execute(
            select(KundaliCore).where(KundaliCore.birth_profile_id == existing_profile.id)
        )
        existing_core = core_result.scalar_one_or_none()

        if existing_core:
            # Load derived for koot_factors
            derived_result = await session.execute(
                select(KundaliDerived).where(KundaliDerived.kundali_core_id == existing_core.id)
            )
            derived = derived_result.scalar_one_or_none()
            koot_factors = derived.koot_factors if derived and derived.koot_factors else {}
            
            return existing_core.id, koot_factors

    # Create new kundali
    service = KundaliService()
    result = await service.create_kundali(
        session=session,
        user_id=user_id,
        payload=details.model_dump(),
    )

    # Get koot_factors from freshly created derived
    derived_result = await session.execute(
        select(KundaliDerived).where(KundaliDerived.kundali_core_id == result["kundali_core_id"])
    )
    derived = derived_result.scalar_one_or_none()
    koot_factors = derived.koot_factors if derived and derived.koot_factors else {}

    return result["kundali_core_id"], koot_factors


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@router.post(
    "/match",
    response_model=MatchResponse,
    summary="Match two Kundalis using Ashta Koot",
)
async def match_kundalis(
    payload: MatchRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Calculate Ashta Koot compatibility between two birth charts.
    
    1. Finds existing kundalis or creates new ones
    2. Calculates matching score
    3. Persists results to database
    4. Returns match_id for Ask AI integration
    """

    # Find or create kundali for boy
    boy_kundali_id, boy_koot = await find_or_create_kundali(
        session, user.id, payload.boy
    )

    # Find or create kundali for girl
    girl_kundali_id, girl_koot = await find_or_create_kundali(
        session, user.id, payload.girl
    )

    # Get Moon data from kundali_core for matching
    boy_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == boy_kundali_id)
    )
    boy_kundali = boy_core.scalar_one()

    girl_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == girl_kundali_id)
    )
    girl_kundali = girl_core.scalar_one()

    # Extract Moon sign and degree
    boy_moon = boy_kundali.planets.get("Moon", {})
    girl_moon = girl_kundali.planets.get("Moon", {})

    # Calculate matching
    matching_service = MatchingService()
    match_result = matching_service.calculate_ashta_koot(
        boy_moon_sign=boy_moon.get("sign", "Aries"),
        boy_moon_degree=boy_moon.get("degree", 0),
        girl_moon_sign=girl_moon.get("sign", "Aries"),
        girl_moon_degree=girl_moon.get("degree", 0),
    )

    # Save to database
    match_repo = KundaliMatchRepository(session)
    match_record = await match_repo.create(
        user_id=user.id,
        boy_kundali_id=boy_kundali_id,
        girl_kundali_id=girl_kundali_id,
        total_score=match_result["total_score"],
        max_score=match_result["max_score"],
        verdict=match_result["verdict"],
        factors=match_result["factors"],
    )

    return MatchResponse(
        match_id=match_record.id,
        boy_kundali_id=boy_kundali_id,
        girl_kundali_id=girl_kundali_id,
        total_score=match_result["total_score"],
        max_score=match_result["max_score"],
        percentage=match_result["percentage"],
        verdict=match_result["verdict"],
        factors=match_result["factors"],
        boy_name=payload.boy.name,
        girl_name=payload.girl.name,
    )


@router.get(
    "/match/{match_id}",
    response_model=MatchResponse,
    summary="Get matching result by ID",
)
async def get_match(
    match_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """Retrieve a previously calculated match."""
    match_repo = KundaliMatchRepository(session)
    match_record = await match_repo.get_by_id(match_id)

    if not match_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Get names from birth profiles
    boy_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.boy_kundali_id)
    )
    girl_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.girl_kundali_id)
    )
    
    boy_kundali = boy_core.scalar_one()
    girl_kundali = girl_core.scalar_one()

    boy_profile = await session.execute(
        select(BirthProfile).where(BirthProfile.id == boy_kundali.birth_profile_id)
    )
    girl_profile = await session.execute(
        select(BirthProfile).where(BirthProfile.id == girl_kundali.birth_profile_id)
    )

    boy_name = boy_profile.scalar_one().name
    girl_name = girl_profile.scalar_one().name

    return MatchResponse(
        match_id=match_record.id,
        boy_kundali_id=match_record.boy_kundali_id,
        girl_kundali_id=match_record.girl_kundali_id,
        total_score=match_record.total_score,
        max_score=match_record.max_score,
        percentage=round((match_record.total_score / match_record.max_score) * 100, 1),
        verdict=match_record.verdict,
        factors=match_record.factors,
        boy_name=boy_name,
        girl_name=girl_name,
    )


# ─────────────────────────────────────────────
# Report Endpoints
# ─────────────────────────────────────────────

@router.get(
    "/report/text/{match_id}",
    summary="Get detailed text report for a match",
)
async def get_match_text_report(
    match_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate a detailed text report with interpretations for each Ashta Koot factor.
    """
    match_repo = KundaliMatchRepository(session)
    match_record = await match_repo.get_by_id(match_id)

    if not match_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Get names from birth profiles
    boy_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.boy_kundali_id)
    )
    girl_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.girl_kundali_id)
    )
    
    boy_kundali = boy_core.scalar_one()
    girl_kundali = girl_core.scalar_one()

    boy_profile = await session.execute(
        select(BirthProfile).where(BirthProfile.id == boy_kundali.birth_profile_id)
    )
    girl_profile = await session.execute(
        select(BirthProfile).where(BirthProfile.id == girl_kundali.birth_profile_id)
    )

    boy_name = boy_profile.scalar_one().name
    girl_name = girl_profile.scalar_one().name

    # Build the report with interpretations
    report_service = MatchingReportService()
    
    match_data = {
        "match_id": str(match_record.id),
        "total_score": match_record.total_score,
        "max_score": match_record.max_score,
        "percentage": round((match_record.total_score / match_record.max_score) * 100, 1),
        "verdict": match_record.verdict,
        "factors": match_record.factors,
    }
    
    report = report_service.build_matching_report(
        match_data=match_data,
        boy_name=boy_name,
        girl_name=girl_name,
    )
    
    return report


@router.get(
    "/report/pdf/{match_id}",
    summary="Download PDF report for a match",
)
async def get_match_pdf_report(
    match_id: UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate and download a PDF report for Kundali matching.
    """
    from fastapi.responses import Response
    from app.services.pdf_service import PDFService
    
    match_repo = KundaliMatchRepository(session)
    match_record = await match_repo.get_by_id(match_id)

    if not match_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    # Get names and birth details from profiles
    boy_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.boy_kundali_id)
    )
    girl_core = await session.execute(
        select(KundaliCore).where(KundaliCore.id == match_record.girl_kundali_id)
    )
    
    boy_kundali = boy_core.scalar_one()
    girl_kundali = girl_core.scalar_one()

    boy_profile_result = await session.execute(
        select(BirthProfile).where(BirthProfile.id == boy_kundali.birth_profile_id)
    )
    girl_profile_result = await session.execute(
        select(BirthProfile).where(BirthProfile.id == girl_kundali.birth_profile_id)
    )

    boy_profile = boy_profile_result.scalar_one()
    girl_profile = girl_profile_result.scalar_one()

    # Build the report with interpretations
    report_service = MatchingReportService()
    
    match_data = {
        "match_id": str(match_record.id),
        "total_score": match_record.total_score,
        "max_score": match_record.max_score,
        "percentage": round((match_record.total_score / match_record.max_score) * 100, 1),
        "verdict": match_record.verdict,
        "factors": match_record.factors,
    }
    
    report = report_service.build_matching_report(
        match_data=match_data,
        boy_name=boy_profile.name,
        girl_name=girl_profile.name,
    )
    
    # Add birth details for PDF
    report["boy_details"] = {
        "name": boy_profile.name,
        "birth_date": str(boy_profile.birth_date) if boy_profile.birth_date else None,
        "birth_time": str(boy_profile.birth_time) if boy_profile.birth_time else None,
        "birth_place": boy_profile.birth_place,
    }
    report["girl_details"] = {
        "name": girl_profile.name,
        "birth_date": str(girl_profile.birth_date) if girl_profile.birth_date else None,
        "birth_time": str(girl_profile.birth_time) if girl_profile.birth_time else None,
        "birth_place": girl_profile.birth_place,
    }
    
    # Generate PDF
    pdf_service = PDFService()
    result = pdf_service.render_matching_pdf(report)
    
    return Response(
        content=result["bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )
