class KundaliError(Exception):
    """
    Base exception for all kundali-related domain errors.
    """
    pass


class InvalidBirthDataError(KundaliError):
    """
    Raised when birth inputs are invalid or inconsistent.
    """
    pass


class UnsupportedAyanamsaError(KundaliError):
    """
    Raised when an unsupported ayanamsa is requested.
    """
    pass


class CalculationError(KundaliError):
    """
    Raised when astronomical calculation fails.
    """
    pass


class KundaliNotFoundError(KundaliError):
    """
    Raised when a kundali or related data cannot be found.
    """
    pass
