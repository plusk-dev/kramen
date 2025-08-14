from datetime import datetime, timezone
from sqlalchemy import inspect

def sqlalchemy_object_to_dict(obj):
    def serialize(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return {
        c.key: serialize(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs
    }

def append_datetime_to_query(query: str) -> str:
    """
    Append current date and time information to the query for temporal context.
    
    The AI agents can use this information if needed for time-sensitive operations
    or ignore it if not relevant to the query.
    
    Args:
        query: The original user query
        
    Returns:
        str: Query with date/time information prepended
    """
    # Get current UTC time
    now_utc = datetime.now(timezone.utc)
    
    # Format date and time in a human-readable way
    formatted_datetime = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    formatted_date = now_utc.strftime("%A, %B %d, %Y")
    
    # Prepend temporal context to the query
    temporal_context = f"[Current date and time: {formatted_datetime} ({formatted_date})]"
    
    return f"{temporal_context}\n\n{query}"
