def is_valid_password(password):
    """
    Checks if a password is valid.
    Requirements: At least 8 characters AND contains a digit.
    BUG: Uses 'or' instead of 'and' - accepts passwords meeting only ONE requirement.
    """
    has_length = len(password) >= 8
    has_digit = any(c.isdigit() for c in password)
    
    # BUG: should be 'and' not 'or'
    return has_length or has_digit
