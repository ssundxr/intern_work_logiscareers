"""
Core Scoring Data Models

This module contains dataclasses used throughout the scoring system.
Separated from comprehensive_scorer to avoid circular imports with strategies.

Author: Senior SDE/ML Architect
Date: January 21, 2026
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class MatchLevel(Enum):
    """Match quality levels for scoring explanations"""
    EXCELLENT = "excellent"
    GOOD = "good"
    PARTIAL = "partial"
    POOR = "poor"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class FieldAssessment:
    """
    Individual field assessment with score and explanation.
    """
    field_name: str
    field_label: str
    candidate_value: Any
    job_requirement: Any
    score: int  # 0-100
    explanation: str
    match_level: MatchLevel
    weight: float = 1.0
    sub_fields: List['FieldAssessment'] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'field_name': self.field_name,
            'field_label': self.field_label,
            'candidate_value': self.candidate_value,
            'job_requirement': self.job_requirement,
            'score': self.score,
            'explanation': self.explanation,
            'match_level': self.match_level.value,
            'weight': self.weight,
            'sub_fields': [sf.to_dict() for sf in self.sub_fields]
        }


@dataclass
class SectionAssessment:
    """
    Section-level assessment aggregating multiple fields.
    """
    section_name: str
    section_label: str
    fields: List[FieldAssessment]
    total_score: int
    weighted_score: float
    explanation: str
    match_level: MatchLevel
    weight: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'section_name': self.section_name,
            'section_label': self.section_label,
            'fields': [f.to_dict() for f in self.fields],
            'total_score': self.total_score,
            'weighted_score': self.weighted_score,
            'explanation': self.explanation,
            'match_level': self.match_level.value,
            'weight': self.weight
        }


@dataclass
class CVAssessment:
    """
    Resume/CV specific assessment.
    """
    cv_score: int
    cv_quality_score: int
    content_relevance_score: int
    keyword_match_score: int
    experience_extraction_score: int
    skills_extraction_score: int
    explanation: str
    matched_keywords: List[str]
    missing_keywords: List[str]
    cv_insights: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'cv_score': self.cv_score,
            'cv_quality_score': self.cv_quality_score,
            'content_relevance_score': self.content_relevance_score,
            'keyword_match_score': self.keyword_match_score,
            'experience_extraction_score': self.experience_extraction_score,
            'skills_extraction_score': self.skills_extraction_score,
            'explanation': self.explanation,
            'matched_keywords': self.matched_keywords,
            'missing_keywords': self.missing_keywords,
            'cv_insights': self.cv_insights
        }


@dataclass
class ComprehensiveAssessmentResult:
    """
    Complete assessment result with all sections and CV analysis.
    """
    total_score: int
    sections: List[SectionAssessment]
    cv_assessment: Optional[CVAssessment]
    is_rejected: bool
    rejection_reasons: List[str]
    overall_explanation: str
    recommendation: str
    confidence_score: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            'total_score': self.total_score,
            'sections': [s.to_dict() for s in self.sections],
            'cv_assessment': self.cv_assessment.to_dict() if self.cv_assessment else None,
            'is_rejected': self.is_rejected,
            'rejection_reasons': self.rejection_reasons,
            'overall_explanation': self.overall_explanation,
            'recommendation': self.recommendation,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp
        }
