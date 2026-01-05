import hashlib
from uuid import UUID


class CacheKeys:
    """
    Centralized cache key builders.
    """

    # ─────────────────────────────────────────────
    # Kundali
    # ─────────────────────────────────────────────

    @staticmethod
    def kundali(user_id: UUID, kundali_core_id: UUID) -> str:
        return f"kundali:{user_id}:{kundali_core_id}"

    # ─────────────────────────────────────────────
    # Ask / AI
    # ─────────────────────────────────────────────

    @staticmethod
    def question_hash(question: str) -> str:
        return hashlib.sha256(question.lower().encode()).hexdigest()

    @staticmethod
    def ask(
        user_id: UUID,
        kundali_core_id: UUID,
        question: str,
    ) -> str:
        qh = CacheKeys.question_hash(question)
        return f"ask:{user_id}:{kundali_core_id}:{qh}"

    # ─────────────────────────────────────────────
    # Report
    # ─────────────────────────────────────────────

    @staticmethod
    def report(
        kundali_core_id: UUID,
        include_transits: bool,
    ) -> str:
        flag = "with_transits" if include_transits else "no_transits"
        return f"report:{kundali_core_id}:{flag}"

    # ─────────────────────────────────────────────
    # Transits
    # ─────────────────────────────────────────────

    @staticmethod
    def transit(kundali_core_id: UUID) -> str:
        return f"transit:{kundali_core_id}"
