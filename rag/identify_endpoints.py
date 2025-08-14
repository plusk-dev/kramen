"""
Backward compatibility module for RAG-based endpoint identification.

This module maintains backward compatibility by importing from the new modular structure.
For new code, prefer importing directly from rag.endpoints and rag.services.
"""

# Import the router from the new endpoints module
from rag.endpoints import run_query_router

# Re-export for backward compatibility
__all__ = ['run_query_router']
