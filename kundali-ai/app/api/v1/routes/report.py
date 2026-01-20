from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.persistence.db import get_db_session
from app.persistence.repositories.kundali_core_repo import KundaliCoreRepository
from app.services.pdf_service import PDFService
from app.services.report_service import ReportService


router = APIRouter()

@router.get("/pdf")
async def get_pdf_report(
    kundali_core_id: UUID,
    include_transits: bool = False,
    language: str = "English",
    session: AsyncSession = Depends(get_db_session),
):
    """
    Generate and download a PDF report for a specific Kundali.
    """
    repo = KundaliCoreRepository(session)
    kundali_core = await repo.get_by_id(kundali_core_id)
    
    if not kundali_core:
        raise HTTPException(status_code=404, detail="Kundali not found")

    # 2. Prepare data
    kundali_chart = kundali_core.to_domain()
    
    # 3. Generate PDF
    # Using a random user_id since this is a public GET endpoint for now
    pdf_service = PDFService()
    report_service = ReportService()

    # First, build the data context
    report_context = await report_service.build_report_context(
        session=session,
        user_id=uuid4(),
        kundali_core_id=kundali_core_id,
        kundali_chart=kundali_chart,
        include_transits=include_transits,
        timestamp=datetime.now(timezone.utc)
    )

    # Then, render the PDF from that context
    result = pdf_service.render_pdf_from_data(report_context)

    return Response(
        content=result["bytes"],
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
    )

@router.post("/pdf_from_data")
async def post_pdf_from_data(report_context: dict):
    """
    Generate a PDF from pre-fetched report data.
    This is faster as it avoids re-calculating everything.
    """
    try:
        pdf_service = PDFService()
        result = pdf_service.render_pdf_from_data(report_context)
        return Response(
            content=result["bytes"],
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to render PDF: {str(e)}")


@router.get("/text")
async def get_text_report(
    kundali_core_id: UUID,
    include_transits: bool = False,
    language: str = "English",
    session: AsyncSession = Depends(get_db_session),
):
    """
    Get the raw JSON data for a Kundali report.
    """
    # 1. Validate Kundali existence
    repo = KundaliCoreRepository(session)
    kundali_core = await repo.get_by_id(kundali_core_id)
    
    if not kundali_core:
        raise HTTPException(status_code=404, detail="Kundali not found")

    # 2. Prepare data
    kundali_chart = kundali_core.to_domain()
    
    # 3. Build Report Context
    service = ReportService()
    report_context = await service.build_report_context(
        session=session,
        user_id=uuid4(),
        kundali_core_id=kundali_core_id,
        kundali_chart=kundali_chart,
        include_transits=include_transits,
        timestamp=datetime.now(timezone.utc),
        language=language
    )

    return _strip_markdown(report_context)

def _strip_markdown(data: Any) -> Any:
    if isinstance(data, str):
        return data.replace("**", "")
    if isinstance(data, dict):
        return {k: _strip_markdown(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_strip_markdown(i) for i in data]
    return data