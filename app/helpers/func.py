def extra_kwargs_constructor(*fields):
    """
    For Constructing extra key arguments
    """
    return {field: {"required": False} for field in fields}
