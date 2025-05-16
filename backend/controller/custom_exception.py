# custom_exceptions.py

from typing import Optional, Dict, Any
from pydantic import BaseModel

class RAGError(Exception):
    """Base exception class for RAG-related errors"""
    def __init__(self, message: str, error_code: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class EmbeddingsError(RAGError):
    """Raised when there are issues with embeddings generation or loading"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "EMBEDDINGS_ERROR", details)

class DataLoadError(RAGError):
    """Raised when there are issues loading the CSV or processing initial data"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATA_LOAD_ERROR", details)

class SearchError(RAGError):
    """Raised when there are issues with the search functionality"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "SEARCH_ERROR", details)

class APIKeyError(RAGError):
    """Raised when there are issues with the OpenAI API key"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "API_KEY_ERROR", details)

class DatabaseError(RAGError):
    """Raised when there are issues with database operations"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "DATABASE_ERROR", details)

class ResponseGenerationError(RAGError):
    """Raised when there are issues generating the final response"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "RESPONSE_GENERATION_ERROR", details)

class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None