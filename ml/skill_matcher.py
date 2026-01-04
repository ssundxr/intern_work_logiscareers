"""
Advanced Skill Matching Engine for Logis AI Candidate Engine

This module provides sophisticated skill matching capabilities including:
- Synonym matching (JS → JavaScript)
- Semantic similarity matching (TensorFlow ≈ PyTorch)
- Category-based matching (Python ecosystem)
- Hierarchical skill taxonomy
- Required vs Preferred skill differentiation

Author: Senior SDE
Date: January 2, 2026
"""

from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from functools import lru_cache
import yaml
import re
from pathlib import Path
import numpy as np
import threading
from sentence_transformers import SentenceTransformer

# Maximum number of skill embeddings to cache (prevents memory leak)
MAX_EMBEDDING_CACHE_SIZE = 10000


@dataclass
class SkillMatch:
    """Represents a match between candidate skill and job requirement"""
    job_skill: str
    candidate_skill: str
    match_type: str  # 'exact', 'synonym', 'semantic', 'category'
    confidence: float  # 0.0 to 1.0
    weight: float  # Applied weight based on match type
    is_required: bool
    category: Optional[str] = None


@dataclass
class SkillMatchResult:
    """Complete skill matching result for a candidate-job pair"""
    matched_required: List[SkillMatch]
    matched_preferred: List[SkillMatch]
    missing_required: List[str]
    missing_preferred: List[str]
    total_required_skills: int
    total_preferred_skills: int
    required_match_score: float  # 0-100
    preferred_match_score: float  # 0-100
    overall_skill_score: float  # Weighted average
    match_details: Dict[str, any]


class SkillMatcher:
    """
    Enterprise-grade skill matching engine with multi-strategy matching.
    
    Matching Strategies (in order of preference):
    1. Exact Match (100% confidence)
    2. Synonym Match (95% confidence) - e.g., "JS" → "JavaScript"
    3. Semantic Match (85% confidence) - e.g., "TensorFlow" ≈ "PyTorch"
    4. Category Match (70% confidence) - e.g., both in "Python ecosystem"
    
    Features:
    - Configurable similarity thresholds
    - Domain-specific skill weights (logistics +20%)
    - Years of experience boost
    - Case-insensitive normalization
    - Special character handling
    """
    
    def __init__(self, config_path: Optional[str] = None, embedding_model: Optional[SentenceTransformer] = None):
        """
        Initialize the SkillMatcher with taxonomy and embedding model.
        
        Args:
            config_path: Path to skills_taxonomy.yaml (auto-detected if None)
            embedding_model: Pre-loaded sentence transformer (will load if None)
        """
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "skills_taxonomy.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Extract configuration sections
        self.synonyms = self.config.get('synonyms', {})
        self.categories = self.config.get('categories', {})
        self.relationships = self.config.get('relationships', {})
        self.weights = self.config.get('weights', {})
        self.matching_config = self.config.get('matching', {})
        self.exclusions = self.config.get('exclusions', {}).get('do_not_match', [])
        
        # Build reverse lookup maps for fast matching
        self._build_lookup_maps()
        
        # Load embedding model for semantic matching
        self.embedding_model = embedding_model
        self._skill_embeddings_cache: Dict[str, np.ndarray] = {}
        self._cache_lock = threading.Lock()  # Thread-safe cache access
        
        # Configuration flags
        self.enable_synonym = self.matching_config.get('enable_synonym_matching', True)
        self.enable_semantic = self.matching_config.get('enable_semantic_matching', True)
        self.enable_category = self.matching_config.get('enable_category_matching', False)
        self.semantic_threshold = self.matching_config.get('semantic_similarity_threshold', 0.75)
    
    def _build_lookup_maps(self):
        """Build reverse lookup maps for efficient matching"""
        # Synonym to canonical skill mapping
        self.synonym_to_canonical: Dict[str, str] = {}
        for canonical, synonyms_list in self.synonyms.items():
            for synonym in synonyms_list:
                normalized = self._normalize_skill(synonym)
                self.synonym_to_canonical[normalized] = canonical
        
        # Skill to category mapping
        self.skill_to_category: Dict[str, str] = {}
        for main_category, subcategories in self.categories.items():
            if isinstance(subcategories, dict):
                for subcategory, skills in subcategories.items():
                    for skill in skills:
                        self.skill_to_category[skill] = f"{main_category}.{subcategory}"
            elif isinstance(subcategories, list):
                for skill in subcategories:
                    self.skill_to_category[skill] = main_category
        
        # Relationship groups (for semantic matching)
        self.skill_to_relationships: Dict[str, List[str]] = {}
        for group_name, skills in self.relationships.items():
            for skill in skills:
                if skill not in self.skill_to_relationships:
                    self.skill_to_relationships[skill] = []
                self.skill_to_relationships[skill].append(group_name)
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name for matching"""
        if not skill:
            return ""
        
        skill = skill.lower().strip()
        
        # Remove special characters if configured
        if self.matching_config.get('strip_special_chars', True):
            skill = re.sub(r'[^\w\s-]', '', skill)
        
        # Normalize whitespace
        skill = ' '.join(skill.split())
        
        return skill
    
    def _get_canonical_skill(self, skill: str) -> str:
        """Get canonical form of skill (handles synonyms)"""
        normalized = self._normalize_skill(skill)
        return self.synonym_to_canonical.get(normalized, normalized)
    
    def _is_excluded_pair(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are in exclusion list"""
        canonical1 = self._get_canonical_skill(skill1)
        canonical2 = self._get_canonical_skill(skill2)
        
        for excluded_pair in self.exclusions:
            if (canonical1 in excluded_pair and canonical2 in excluded_pair):
                return True
        return False
    
    def _get_skill_embedding(self, skill: str) -> Optional[np.ndarray]:
        """Get embedding for a skill (with thread-safe LRU caching)"""
        if self.embedding_model is None:
            return None
        
        canonical = self._get_canonical_skill(skill)
        
        # Thread-safe cache access
        with self._cache_lock:
            if canonical in self._skill_embeddings_cache:
                return self._skill_embeddings_cache[canonical]
            
            # Evict oldest entries if cache is full (simple LRU)
            if len(self._skill_embeddings_cache) >= MAX_EMBEDDING_CACHE_SIZE:
                # Remove first 10% of entries
                keys_to_remove = list(self._skill_embeddings_cache.keys())[:MAX_EMBEDDING_CACHE_SIZE // 10]
                for key in keys_to_remove:
                    del self._skill_embeddings_cache[key]
        
        # Generate embedding (outside lock to allow parallel encoding)
        embedding = self.embedding_model.encode([canonical])[0]
        
        # Store in cache
        with self._cache_lock:
            self._skill_embeddings_cache[canonical] = embedding
        
        return embedding
    
    def _calculate_semantic_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate semantic similarity between two skills using embeddings"""
        if not self.enable_semantic or self.embedding_model is None:
            return 0.0
        
        # Check exclusions first
        if self._is_excluded_pair(skill1, skill2):
            return 0.0
        
        emb1 = self._get_skill_embedding(skill1)
        emb2 = self._get_skill_embedding(skill2)
        
        if emb1 is None or emb2 is None:
            return 0.0
        
        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        return float(similarity)
    
    def _match_single_skill(
        self, 
        job_skill: str, 
        candidate_skills: List[str],
        is_required: bool = True
    ) -> Optional[SkillMatch]:
        """
        Match a single job skill against candidate skills using multiple strategies.
        
        Returns the best match or None if no match found.
        """
        job_normalized = self._normalize_skill(job_skill)
        job_canonical = self._get_canonical_skill(job_skill)
        best_match: Optional[SkillMatch] = None
        best_confidence = 0.0
        
        for candidate_skill in candidate_skills:
            candidate_normalized = self._normalize_skill(candidate_skill)
            candidate_canonical = self._get_canonical_skill(candidate_skill)
            
            # Strategy 1: True Exact Match (before any synonym mapping)
            if job_normalized == candidate_normalized:
                match = SkillMatch(
                    job_skill=job_skill,
                    candidate_skill=candidate_skill,
                    match_type='exact',
                    confidence=1.0,
                    weight=self.weights['match_type_weights']['exact_match'],
                    is_required=is_required,
                    category=self.skill_to_category.get(job_canonical)
                )
                return match  # Exact match is best, return immediately
            
            # Strategy 2: Synonym Match (same canonical form but different input)
            if self.enable_synonym:
                if (job_canonical == candidate_canonical and 
                    job_normalized != candidate_normalized):  # Different input, same meaning
                    confidence = 0.95
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = SkillMatch(
                            job_skill=job_skill,
                            candidate_skill=candidate_skill,
                            match_type='synonym',
                            confidence=confidence,
                            weight=self.weights['match_type_weights']['synonym_match'],
                            is_required=is_required,
                            category=self.skill_to_category.get(job_canonical)
                        )
            
            # Strategy 3: Semantic Match (using embeddings)
            if self.enable_semantic:
                semantic_sim = self._calculate_semantic_similarity(job_skill, candidate_skill)
                if semantic_sim >= self.semantic_threshold:
                    confidence = semantic_sim * 0.85  # Scale to 0.85 max
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = SkillMatch(
                            job_skill=job_skill,
                            candidate_skill=candidate_skill,
                            match_type='semantic',
                            confidence=confidence,
                            weight=self.weights['match_type_weights']['semantic_match'],
                            is_required=is_required,
                            category=self.skill_to_category.get(job_canonical)
                        )
            
            # Strategy 4: Category Match (same category/relationship group)
            if self.enable_category:
                job_relationships = self.skill_to_relationships.get(job_canonical, [])
                candidate_relationships = self.skill_to_relationships.get(candidate_canonical, [])
                
                common_relationships = set(job_relationships) & set(candidate_relationships)
                if common_relationships:
                    confidence = 0.7
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = SkillMatch(
                            job_skill=job_skill,
                            candidate_skill=candidate_skill,
                            match_type='category',
                            confidence=confidence,
                            weight=self.weights['match_type_weights']['category_match'],
                            is_required=is_required,
                            category=list(common_relationships)[0]
                        )
        
        return best_match
    
    def match_skills(
        self,
        required_job_skills: List[str],
        preferred_job_skills: List[str],
        candidate_skills: List[str]
    ) -> SkillMatchResult:
        """
        Match candidate skills against job requirements (required + preferred).
        
        Args:
            required_job_skills: Must-have skills for the job
            preferred_job_skills: Nice-to-have skills
            candidate_skills: Skills from candidate's profile
        
        Returns:
            SkillMatchResult with detailed matching information
        """
        matched_required: List[SkillMatch] = []
        matched_preferred: List[SkillMatch] = []
        missing_required: List[str] = []
        missing_preferred: List[str] = []
        
        # Match required skills
        for job_skill in required_job_skills:
            match = self._match_single_skill(job_skill, candidate_skills, is_required=True)
            if match:
                matched_required.append(match)
            else:
                missing_required.append(job_skill)
        
        # Match preferred skills
        for job_skill in preferred_job_skills:
            match = self._match_single_skill(job_skill, candidate_skills, is_required=False)
            if match:
                matched_preferred.append(match)
            else:
                missing_preferred.append(job_skill)
        
        # Calculate scores
        total_required = len(required_job_skills)
        total_preferred = len(preferred_job_skills)
        
        # Edge case: Candidate has no skills at all
        if not candidate_skills and (total_required > 0 or total_preferred > 0):
            return SkillMatchResult(
                matched_required=[],
                matched_preferred=[],
                missing_required=required_job_skills,
                missing_preferred=preferred_job_skills,
                total_required_skills=total_required,
                total_preferred_skills=total_preferred,
                required_match_score=0.0,
                preferred_match_score=0.0,
                overall_skill_score=0.0,
                match_details={
                    'exact_matches': 0,
                    'synonym_matches': 0,
                    'semantic_matches': 0,
                    'category_matches': 0,
                    'required_match_rate': 0.0,
                    'preferred_match_rate': 0.0
                }
            )
        
        # Required skill score (weighted by match confidence)
        if total_required > 0:
            required_score_sum = sum(match.confidence * match.weight for match in matched_required)
            required_match_score = (required_score_sum / total_required) * 100
        else:
            required_match_score = 100.0  # No required skills = perfect score
        
        # Preferred skill score (weighted by match confidence)
        if total_preferred > 0:
            preferred_score_sum = sum(match.confidence * match.weight for match in matched_preferred)
            preferred_match_score = (preferred_score_sum / total_preferred) * 100
        else:
            preferred_match_score = 100.0  # No preferred skills = perfect score
        
        # Overall skill score (required skills weighted more heavily)
        # 70% required, 30% preferred
        overall_skill_score = (required_match_score * 0.7) + (preferred_match_score * 0.3)
        
        # Build detailed match information
        match_details = {
            'exact_matches': len([m for m in matched_required + matched_preferred if m.match_type == 'exact']),
            'synonym_matches': len([m for m in matched_required + matched_preferred if m.match_type == 'synonym']),
            'semantic_matches': len([m for m in matched_required + matched_preferred if m.match_type == 'semantic']),
            'category_matches': len([m for m in matched_required + matched_preferred if m.match_type == 'category']),
            'required_match_rate': len(matched_required) / total_required if total_required > 0 else 1.0,
            'preferred_match_rate': len(matched_preferred) / total_preferred if total_preferred > 0 else 1.0
        }
        
        return SkillMatchResult(
            matched_required=matched_required,
            matched_preferred=matched_preferred,
            missing_required=missing_required,
            missing_preferred=missing_preferred,
            total_required_skills=total_required,
            total_preferred_skills=total_preferred,
            required_match_score=required_match_score,
            preferred_match_score=preferred_match_score,
            overall_skill_score=overall_skill_score,
            match_details=match_details
        )
    
    def get_skill_recommendations(
        self, 
        missing_required: List[str], 
        missing_preferred: List[str],
        limit: int = 5
    ) -> List[Tuple[str, str, str]]:
        """
        Generate skill improvement recommendations.
        
        Returns:
            List of (skill, reason, priority) tuples
        """
        recommendations = []
        
        # Required skills have highest priority
        for skill in missing_required[:limit]:
            category = self.skill_to_category.get(self._get_canonical_skill(skill), 'General')
            recommendations.append((
                skill,
                f"Required skill in {category} category",
                "critical"
            ))
        
        # Preferred skills have medium priority
        remaining = limit - len(recommendations)
        for skill in missing_preferred[:remaining]:
            category = self.skill_to_category.get(self._get_canonical_skill(skill), 'General')
            recommendations.append((
                skill,
                f"Preferred skill in {category} category - would strengthen application",
                "high"
            ))
        
        return recommendations
    
    def explain_match(self, match: SkillMatch) -> str:
        """Generate human-readable explanation for a skill match"""
        explanations = {
            'exact': f"Perfect match: '{match.candidate_skill}' exactly matches required '{match.job_skill}'",
            'synonym': f"Synonym match: '{match.candidate_skill}' is equivalent to '{match.job_skill}'",
            'semantic': f"Related skill: '{match.candidate_skill}' is similar to '{match.job_skill}' ({match.confidence:.0%} match)",
            'category': f"Category match: '{match.candidate_skill}' is in the same category as '{match.job_skill}'"
        }
        return explanations.get(match.match_type, f"Matched '{match.candidate_skill}' to '{match.job_skill}'")


# Singleton instance for global access
_skill_matcher_instance: Optional[SkillMatcher] = None


def get_skill_matcher(embedding_model: Optional[SentenceTransformer] = None) -> SkillMatcher:
    """Get or create singleton SkillMatcher instance"""
    global _skill_matcher_instance
    
    if _skill_matcher_instance is None:
        _skill_matcher_instance = SkillMatcher(embedding_model=embedding_model)
    
    return _skill_matcher_instance
