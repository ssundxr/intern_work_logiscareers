"""
Pipeline Abstraction for CV Parsing

This module defines the core pipeline architecture:
- ParserStage: Abstract base class for all parsing stages
- ParsingContext: Shared state object passed through the pipeline
- Pipeline: Orchestrator that executes stages in sequence

Design Principles:
1. Each stage is independent and testable
2. Context holds ALL intermediate state (no globals)
3. Stages communicate ONLY through context
4. Errors are stage-specific and traceable
5. Pipeline is generic and reusable

Pipeline Flow:
    Input → Stage1(context) → Stage2(context) → ... → Output
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


# =============================================================================
# PARSING CONTEXT
# =============================================================================

@dataclass
class ParsingContext:
    """
    Shared state object passed through all parsing stages.
    
    This object accumulates parsed data and intermediate results as it flows
    through the pipeline. Each stage reads from and writes to this context.
    
    Attributes:
        raw_text: Original CV text (immutable)
        cleaned_text: Normalized/cleaned text (set by TextCleaner)
        sections: CV sections (set by SectionSegmenter)
        entities: Extracted entities (contact, name, etc.)
        experiences: Parsed work history
        education: Parsed education
        skills: Extracted skills
        metadata: Stage-specific metadata
        warnings: Parsing warnings/errors
    """
    
    # Input (immutable)
    raw_text: str
    
    # Cleaned text (set by TextCleaner)
    cleaned_text: Optional[str] = None
    
    # Sections (set by SectionSegmenter)
    sections: Dict[str, str] = field(default_factory=dict)
    
    # Entities (set by EntityExtractor)
    entities: Dict[str, Any] = field(default_factory=dict)
    
    # Experiences (set by ExperienceExtractor)
    experiences: List[Any] = field(default_factory=list)
    
    # Education (set by EducationExtractor)
    education: List[Any] = field(default_factory=list)
    
    # Skills (set by SkillNormalizer)
    skills: List[Any] = field(default_factory=list)
    
    # Certifications
    certifications: List[Any] = field(default_factory=list)
    
    # Languages
    languages: List[str] = field(default_factory=list)
    
    # Metadata (for debugging/tracing)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Warnings/errors from stages
    warnings: List[str] = field(default_factory=list)
    
    def add_warning(self, stage_name: str, message: str) -> None:
        """Add a parsing warning with stage context."""
        self.warnings.append(f"[{stage_name}] {message}")
    
    def set_metadata(self, stage_name: str, key: str, value: Any) -> None:
        """Set stage-specific metadata for debugging."""
        if stage_name not in self.metadata:
            self.metadata[stage_name] = {}
        self.metadata[stage_name][key] = value


# =============================================================================
# PARSER STAGE BASE CLASS
# =============================================================================

class ParserStage(ABC):
    """
    Abstract base class for all parsing stages.
    
    Each stage implements a specific parsing responsibility:
    - TextCleaner: Normalizes raw text
    - SectionSegmenter: Identifies CV sections
    - EntityExtractor: Extracts contact info, name, etc.
    - SkillNormalizer: Extracts and normalizes skills
    
    Stages MUST:
    - Implement process(context) method
    - Raise ParsingStageError on failures
    - NOT modify context.raw_text
    - NOT access global state
    
    Stages SHOULD:
    - Log metadata for debugging
    - Add warnings for recoverable issues
    - Be independently testable
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Stage name for logging and error reporting.
        
        Returns:
            Human-readable stage name (e.g., "TextCleaner", "EntityExtractor")
        """
        pass
    
    @abstractmethod
    def process(self, context: ParsingContext) -> None:
        """
        Execute this parsing stage.
        
        This method modifies the context object in-place, adding parsed data
        and metadata. It should NEVER modify context.raw_text.
        
        Args:
            context: Parsing context containing input and accumulated results
            
        Raises:
            ParsingStageError: If stage encounters unrecoverable error
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"


# =============================================================================
# PARSING EXCEPTIONS
# =============================================================================

class ParsingStageError(Exception):
    """
    Exception raised when a parsing stage fails.
    
    This exception includes:
    - Stage name (which stage failed)
    - Error message (what went wrong)
    - Original exception (if any)
    
    This makes debugging much easier by identifying exactly where in the
    pipeline the failure occurred.
    """
    
    def __init__(
        self, 
        stage_name: str, 
        message: str, 
        original_exception: Optional[Exception] = None
    ):
        self.stage_name = stage_name
        self.original_exception = original_exception
        
        full_message = f"[{stage_name}] {message}"
        if original_exception:
            full_message += f" (caused by: {type(original_exception).__name__}: {original_exception})"
        
        super().__init__(full_message)


# =============================================================================
# PIPELINE
# =============================================================================

class Pipeline:
    """
    Generic pipeline that executes parsing stages in sequence.
    
    The pipeline:
    1. Creates a ParsingContext from input
    2. Executes each stage in order
    3. Each stage modifies the context
    4. Returns the final context
    
    Stages are executed in the order they were added. If a stage raises
    ParsingStageError, the pipeline stops and propagates the error.
    
    Usage:
        pipeline = Pipeline()
        pipeline.add_stage(TextCleaner())
        pipeline.add_stage(SectionSegmenter())
        
        context = pipeline.execute(raw_text)
        print(context.sections)
    """
    
    def __init__(self):
        self._stages: List[ParserStage] = []
    
    def add_stage(self, stage: ParserStage) -> Pipeline:
        """
        Add a parsing stage to the pipeline.
        
        Stages are executed in the order they are added.
        
        Args:
            stage: Parser stage to add
            
        Returns:
            self (for method chaining)
        """
        self._stages.append(stage)
        return self
    
    def execute(self, raw_text: str) -> ParsingContext:
        """
        Execute the pipeline on raw CV text.
        
        Args:
            raw_text: Raw CV text to parse
            
        Returns:
            ParsingContext with all parsed data
            
        Raises:
            ParsingStageError: If any stage fails
        """
        # Create context
        context = ParsingContext(raw_text=raw_text)
        
        # Execute each stage
        for stage in self._stages:
            try:
                stage.process(context)
            except ParsingStageError:
                # Re-raise stage errors as-is
                raise
            except Exception as e:
                # Wrap unexpected errors in ParsingStageError
                raise ParsingStageError(
                    stage_name=stage.name,
                    message=f"Unexpected error: {str(e)}",
                    original_exception=e
                )
        
        return context
    
    def get_stages(self) -> List[ParserStage]:
        """Get list of all stages in this pipeline."""
        return self._stages.copy()
    
    def __repr__(self) -> str:
        stage_names = [stage.name for stage in self._stages]
        return f"<Pipeline: {' → '.join(stage_names)}>"
