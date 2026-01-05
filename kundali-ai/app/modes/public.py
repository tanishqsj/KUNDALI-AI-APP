from fastapi import APIRouter, Depends, HTTPException

from app.services.kundali_service import KundaliService
from app.services.ai_service import AIService
from app.services.pdf_service import PDFService
from app.services.billing_service import BillingService
from app.api.dependencies import get_current_user


router = APIRouter(
    prefix="/public",
    tags=["Public"],
)


# ─────────────────────────────────────────────
# Kundali Generation
# ─────────────────────────────────────────────

@router.post("/kundali")
async def generate_kundali(
    payload: dict,
    user=Depends(get_current_user),
    kundali_service: KundaliService = Depends(),
    billing_service: BillingService = Depends(),
):
    """
    Generate kundali for a user.
    """
    billing_service.assert_quota(user.id, feature="kundali")

    kundali = await kundali_service.generate(
        user_id=user.id,
        payload=payload,
    )

    billing_service.log_usage(user.id, feature="kundali")
    return kundali


# ─────────────────────────────────────────────
# Ask AI
# ─────────────────────────────────────────────

@router.post("/ask")
async def ask_astrology(
    question: str,
    user=Depends(get_current_user),
    ai_service: AIService = Depends(),
    billing_service: BillingService = Depends(),
):
    """
    Ask astrology question powered by AI.
    """
    billing_service.assert_quota(user.id, feature="ask_llm")

    answer = await ai_service.ask(
        user_id=user.id,
        question=question,
    )

    billing_service.log_usage(user.id, feature="ask_llm")
    return {"answer": answer}


# ─────────────────────────────────────────────
# PDF Report
# ─────────────────────────────────────────────

@router.get("/kundali/{kundali_id}/pdf")
async def download_pdf(
    kundali_id: str,
    user=Depends(get_current_user),
    pdf_service: PDFService = Depends(),
    billing_service: BillingService = Depends(),
):
    """
    Download kundali PDF report.
    """
    billing_service.assert_quota(user.id, feature="pdf_report")

    pdf = await pdf_service.generate(kundali_id, user.id)

    billing_service.log_usage(user.id, feature="pdf_report")
    return pdf
