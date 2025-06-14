



def create_response(code=0, data=None, message="Success"):
    """
    Create a standardized response object.
    
    Args:
        code (int): Response code (0 for success, non-zero for errors)
                   Common codes:
                   - 0: Success
                   - 400: Bad Request
                   - 401: Unauthorized
                   - 404: Not Found
                   - 409: Conflict (e.g., already exists)
                   - 500: Internal Server Error
        data (dict|list|None): Response data payload
        message (str): Human-readable message
        
    Returns:
        dict: Standardized response object
    """
    return {
        "code": code,
        "data": data,
        "msg": message
    }


def success_response(data=None, message="Success"):
    """
    Shorthand for creating a successful response.
    
    Args:
        data (dict|list|None): Response data
        message (str): Success message
        
    Returns:
        dict: Success response object
    """
    return create_response(code=0, data=data, message=message)


def error_response(code, message, data=None):
    """
    Shorthand for creating an error response.
    
    Args:
        code (int): Error code (should be non-zero)
        message (str): Error message
        data (dict|None): Optional error details
        
    Returns:
        dict: Error response object
    """
    return create_response(code=code, data=data, message=message)