"""
ML Parser Package

Pipeline-based CV parsing architecture with clearly defined stages.

This package decomposes CV parsing into modular, testable components:
- Pipeline: Orchestration framework
- Context: Shared state object passed through stages
- Stages: Independent parsing units (TextCleaner, SectionSegmenter, etc.)
- Patterns: Centralized regex definitions

Architecture:
    CVParser → Pipeline → [Stage1, Stage2, ...] → ParsedCV
"""

__all__ = [
    'Pipeline',
    'ParsingContext',
    'ParserStage',
    'ParsingStageError',
    'CVParsingPipeline',
    'TextCleaner',
    'SectionSegmenter',
    'EntityExtractor',
    'SkillNormalizer',
    'ExperienceExtractor',
    'EducationExtractor',
]

from .pipeline import Pipeline, ParserStage, ParsingContext, ParsingStageError
from .cv_pipeline import CVParsingPipeline
from .text_cleaner import TextCleaner
from .section_segmenter import SectionSegmenter
from .entity_extractor import EntityExtractor
from .skill_normalizer import SkillNormalizer
from .experience_extractor import ExperienceExtractor
from .education_extractor import EducationExtractor

