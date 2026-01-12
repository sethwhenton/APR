def count_positives(numbers):
    """
    Counts how many positive numbers are in the list.
    BUG: Uses '<' instead of '>' to check for positive, counting
    negative numbers instead of positive ones.
    """
    if not numbers:
        return 0
    
    count = 0
    for n in numbers:
        if n < 0:  # BUG: should be > 0 to count positives
            count += 1
            
    return count
