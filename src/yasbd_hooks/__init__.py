"""Opt-in, paragraph-local post-processing hooks for YASBD."""
from ._types import Hook, HookContext
from .bracketed_citations import bracketed_citations
from .academic_citations import academic_citations
from .chemical_notation import chemical_notation
from .clause_boundaries import clause_boundaries
from .compose_hooks import compose_hooks
from .ocr_artifacts import ocr_artifacts

__all__ = ['bracketed_citations', 'chemical_notation', 'academic_citations', 'clause_boundaries',
           'ocr_artifacts', 'compose_hooks', 'HookContext', 'Hook']
