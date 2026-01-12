def find_max(numbers):
    """
    Intended to find the maximum value in a list of numbers.
    However, it contains a logic bug.
    """
    if not numbers:
        return None
        
    current = numbers[0]
    # BUG: This should be 'if n > current:'. Using '<' causes it to find the minimum.
    for n in numbers[1:]:
        if n < current:
            current = n
            
    return current
