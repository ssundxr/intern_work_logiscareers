"""
SkillNormalizer Stage

Extracts and normalizes skills from CV text using the skill taxonomy.

This stage extracts the SkillExtractor logic from the original cv_parser.py
and adapts it to the pipeline architecture. ALL skill extraction logic is
preserved exactly.

Skill Extraction Strategy:
1. Direct matching against taxonomy (exact/fuzzy)
2. Pattern matching (bullet points, comma lists)
3. Normalization using synonyms
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..cv_parser import SkillExtraction
from .pipeline import ParserStage, ParsingContext, ParsingStageError


class SkillNormalizer(ParserStage):
    """
    Fourth stage in the parsing pipeline - extracts and normalizes skills.
    
    This stage extracts skills from CV sections using:
    - Taxonomy-based matching
    - Pattern matching (bullet points, comma lists)
    - Synonym normalization
    
    The logic is extracted directly from the original SkillExtractor class
    with NO modifications to preserve exact behavior.
    """
    
    _taxonomy: Optional[Dict] = None
    _all_skills: Optional[Set[str]] = None
    
    @property
    def name(self) -> str:
        return "SkillNormalizer"
    
    @classmethod
    def _load_taxonomy(cls) -> Dict:
        """
        Load skill taxonomy from YAML file.
        
        This method is IDENTICAL to SkillExtractor._load_taxonomy()
        """
        if cls._taxonomy is None:
            taxonomy_path = Path(__file__).parent.parent.parent / 'config' / 'skills_taxonomy.yaml'
            
            if taxonomy_path.exists():
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    cls._taxonomy = yaml.safe_load(f)
            else:
                cls._taxonomy = {'synonyms': {}, 'categories': {}}
        
        return cls._taxonomy
    
    @classmethod
    def _get_all_skills(cls) -> Set[str]:
        """
        Get all known skills from taxonomy (including synonyms).
        
        This method is IDENTICAL to SkillExtractor._get_all_skills()
        """
        if cls._all_skills is None:
            taxonomy = cls._load_taxonomy()
            skills = set()
            
            # Add all canonical skills
            for canonical, synonyms in taxonomy.get('synonyms', {}).items():
                skills.add(canonical.lower())
                for syn in synonyms:
                    skills.add(syn.lower())
            
            cls._all_skills = skills
        
        return cls._all_skills
    
    @classmethod
    def _normalize_skill(cls, skill: str) -> str:
        """
        Normalize a skill string.
        
        This method is IDENTICAL to SkillExtractor._normalize_skill()
        """
        taxonomy = cls._load_taxonomy()
        skill_lower = skill.lower().strip()
        
        # Check if it's a synonym and return canonical form
        for canonical, synonyms in taxonomy.get('synonyms', {}).items():
            if skill_lower in [s.lower() for s in synonyms]:
                return canonical
        
        return skill_lower
    
    def extract_skills(
        self, 
        text: str, 
        section: str = 'unknown'
    ) -> List[SkillExtraction]:
        """
        Extract skills from text using multiple strategies.
        
        This method is IDENTICAL to SkillExtractor.extract_skills()
        
        Strategies:
        1. Direct matching against taxonomy
        2. Pattern matching for common skill formats
        3. Context-aware extraction
        """
        extracted = []
        seen_normalized = set()
        all_skills = self._get_all_skills()
        
        # Strategy 1: Direct matching against known skills
        text_lower = text.lower()
        
        for skill in all_skills:
            # Use word boundary matching to avoid partial matches
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                normalized = self._normalize_skill(skill)
                
                if normalized not in seen_normalized:
                    extracted.append(SkillExtraction(
                        skill=skill,
                        normalized_skill=normalized,
                        confidence=1.0,
                        source_section=section,
                    ))
                    seen_normalized.add(normalized)
        
        # Strategy 2: Extract from skill-like patterns (bullet points, comma lists)
        skill_list_pattern = re.compile(
            r'(?:^|\n)\s*[-•*]\s*([^:\n]+?)(?:\n|$)|'  # Bullet points
            r'(?:skills?|technologies?|tools?)[\s:]+([^.\n]+)',  # After "skills:"
            re.IGNORECASE
        )
        
        for match in skill_list_pattern.finditer(text):
            matched_text = match.group(1) or match.group(2)
            if matched_text:
                # Split by common delimiters
                potential_skills = re.split(r'[,;|/]', matched_text)
                
                for skill_candidate in potential_skills:
                    skill_clean = skill_candidate.strip()
                    
                    if skill_clean and 2 <= len(skill_clean) <= 50:
                        skill_lower = skill_clean.lower()
                        
                        # Check if it matches any known skill
                        for known_skill in all_skills:
                            if known_skill in skill_lower or skill_lower in known_skill:
                                normalized = self._normalize_skill(known_skill)
                                
                                if normalized not in seen_normalized:
                                    extracted.append(SkillExtraction(
                                        skill=skill_clean,
                                        normalized_skill=normalized,
                                        confidence=0.9,
                                        source_section=section,
                                    ))
                                    seen_normalized.add(normalized)
                                break
        
        return extracted
    
    def process(self, context: ParsingContext) -> None:
        """
        Extract and normalize skills from CV sections.
        
        Args:
            context: Parsing context with sections
            
        Updates:
            context.skills: List of SkillExtraction objects
            
        Raises:
            ParsingStageError: If skill extraction fails
        """
        try:
            sections = context.sections
            
            if not sections:
                context.add_warning(self.name, "No sections available for skill extraction")
                return
            
            # Extract skills from all sections (same logic as CVParser.parse())
            all_skills = []
            
            # Prioritize skills section
            if 'skills' in sections:
                all_skills.extend(
                    self.extract_skills(sections['skills'], 'skills')
                )
            
            # Also check experience and summary for skills
            for section_name in ['experience', 'summary', 'header']:
                if section_name in sections:
                    section_skills = self.extract_skills(
                        sections[section_name], section_name
                    )
                    # Only add if not already found
                    existing_normalized = {s.normalized_skill for s in all_skills}
                    for skill in section_skills:
                        if skill.normalized_skill not in existing_normalized:
                            all_skills.append(skill)
                            existing_normalized.add(skill.normalized_skill)
            
            context.skills = all_skills
            context.set_metadata(self.name, "skill_count", len(all_skills))
            context.set_metadata(self.name, "unique_skills", len(set(s.normalized_skill for s in all_skills)))
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Skill extraction failed: {str(e)}",
                original_exception=e
            )
