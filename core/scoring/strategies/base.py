"""
Base Strategy Interface for Scoring Strategies

This module defines the abstract base class that all scoring strategies must implement.
Each strategy is responsible for ONE specific assessment concern.

Follows: Strategy Pattern (GoF Design Patterns)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class ScoringContext:
    """
    Context object passed to scoring strategies.
    Contains all data needed for assessment without exposing implementation details.
    """
    candidate_data: Dict[str, Any]
    job_data: Dict[str, Any]
    cv_text: str = ""
    
    def __post_init__(self):
        """Ensure data dictionaries are not None"""
        if self.candidate_data is None:
            self.candidate_data = {}
        if self.job_data is None:
            self.job_data = {}


class ScoringStrategy(ABC):
    """
    Abstract base class for all scoring strategies.
    
    Each concrete strategy implements a single assessment responsibility
    (e.g., skills assessment, experience assessment, etc.)
    
    Design Principles:
    - Single Responsibility: Each strategy handles ONE assessment type
    - Open/Closed: New strategies can be added without modifying existing code
    - Dependency Inversion: ComprehensiveScorer depends on abstraction, not concrete strategies
    """
    
    @abstractmethod
    def score(self, context: ScoringContext) -> Any:
        """
        Perform scoring assessment based on the provided context.
        
        Args:
            context: ScoringContext containing candidate_data, job_data, and optional cv_text
        
        Returns:
            Assessment result (type depends on strategy implementation)
            
        Note:
            This method must be implemented by all concrete strategy classes.
            The return type may vary by strategy (e.g., SectionAssessment, CVAssessment)
        """
        pass
