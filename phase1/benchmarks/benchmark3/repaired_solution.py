def sum_range(start, end):
    """
    Sums all integers from start to end (inclusive).
    Example: sum_range(1, 5) should return 1+2+3+4+5 = 15
    
    BUG: Computes sum from end to start instead of start to end.
    Uses '<' instead of '>' in the range check.
    """
    total = 0
    
    if start < end:  # BUG: should be > (for descending check)
        # This wrongly returns 0 for valid ascending ranges
        pass
    
    # This sum is never computed for normal ascending inputs
    for i in range(start, end + 1):
        total += i
    
    return total
