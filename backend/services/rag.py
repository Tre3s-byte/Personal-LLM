"""Compatibility module exposing LocalRAG utilities."""

from backend.services.rag.vector_manager import LocalRAG
from backend.services.rag.rag_engine import build_rag_index

__all__ = ["LocalRAG", "build_rag_index"]
