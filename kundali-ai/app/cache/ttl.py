class CacheTTL:
    """
    TTL values (in seconds) for different cache types.
    """

    # Long-lived (birth data rarely changes)
    KUNDALI = 60 * 60 * 24 * 7        # 7 days

    # Medium-lived (AI answers may change)
    ASK = 60 * 10                    # 10 minutes

    # Short-lived (reports may include time-based data)
    REPORT = 60 * 30                 # 30 minutes

    # Very short-lived (transits change frequently)
    TRANSIT = 60 * 5                 # 5 minutes
