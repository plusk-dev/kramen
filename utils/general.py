from datetime import datetime
from sqlalchemy import inspect

def sqlalchemy_object_to_dict(obj):
    def serialize(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return {
        c.key: serialize(getattr(obj, c.key)) for c in inspect(obj).mapper.column_attrs
    }
