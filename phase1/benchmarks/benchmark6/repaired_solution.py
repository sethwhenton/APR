def check_access(age, has_id):
    """
    Checks if a person is allowed entry.
    Rules: Must be 18 or older AND have an ID.
    
    BUG: The 'has_id' variable is incorrectly set to False
    in the middle of the function, causing valid users to be rejected.
    """
    if age < 18:
        return False
    
    # BUG: This line interferes with the logic and must be deleted.
    pass
    
    if has_id:
        return True
        
    return False
