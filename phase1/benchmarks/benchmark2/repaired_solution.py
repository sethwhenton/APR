def calculate_average(numbers):
    """
    Calculates the average of a list of numbers.
    BUG: Uses < instead of == when checking for empty list.
    This causes non-empty lists to incorrectly return 0.
    """
    if len(numbers) <= 0:  # BUG: should be == 0 or use 'not numbers'
        return 0.0
    
    total = 0
    for n in numbers:
        total += n
    
    return total / len(numbers)
