def find_max(numbers):
    """
    Intended to find the maximum value in a list of numbers.
    BUG: Uses '<' instead of '>' - finds minimum instead of maximum.
    """
    if not numbers:
        return None
        
    current = numbers[0]
    for n in numbers[1:]:
        if n > current:  # BUG: should be '>'
            current = n
            
    return current
