"""
CVParsingPipeline Orchestrator

Assembles all parsing stages into a complete CV parsing pipeline.

This orchestrator:
1. Creates the pipeline with all stages in correct order
2. Executes the pipeline on raw CV text
3. Converts ParsingContext to ParsedCV
4. Handles additional post-processing (languages, confidence)

Pipeline Stages (in order):
1. TextCleaner - normalizes raw text
2. SectionSegmenter - segments into sections
3. EntityExtractor - extracts contact/name/summary
4. SkillNormalizer - extracts and normalizes skills
5. ExperienceExtractor - extracts work history
6. EducationExtractor - extracts education
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..cv_parser import ParsedCV, ContactInfo
from .pipeline import Pipeline, ParsingContext
from .text_cleaner import TextCleaner
from .section_segmenter import SectionSegmenter
from .entity_extractor import EntityExtractor
from .skill_normalizer import SkillNormalizer
from .experience_extractor import ExperienceExtractor
from .education_extractor import EducationExtractor
from .patterns import KNOWN_LANGUAGES


class CVParsingPipeline:
    """
    Orchestrates the complete CV parsing pipeline.
    
    This class assembles all parsing stages and provides a high-level
    interface for parsing CVs. It replaces the original CVParser's
    internal logic with a modular pipeline architecture.
    
    The pipeline preserves EXACT behavior from the original cv_parser.py.
    """
    
    def __init__(self):
        """Initialize the CV parsing pipeline with all stages."""
        self.pipeline = Pipeline()
        
        # Add stages in correct order (matching CVParser.parse() steps)
        self.pipeline.add_stage(TextCleaner())          # Step 0: Clean text
        self.pipeline.add_stage(SectionSegmenter())     # Step 1: Segment sections
        self.pipeline.add_stage(EntityExtractor())      # Steps 2-4: Contact, name, summary
        self.pipeline.add_stage(SkillNormalizer())      # Step 5: Skills
        self.pipeline.add_stage(ExperienceExtractor())  # Step 6: Experience
        self.pipeline.add_stage(EducationExtractor())   # Step 7: Education
    
    def parse(self, text: str) -> ParsedCV:
        """
        Parse CV text and extract all structured information.
        
        This method replaces CVParser.parse() with pipeline-based logic.
        The output is IDENTICAL to the original implementation.
        
        Args:
            text: Raw CV text content
            
        Returns:
            ParsedCV object containing all extracted information
        """
        result = ParsedCV(raw_text=text)
        
        try:
            # Execute pipeline
            context = self.pipeline.execute(text)
            
            # Convert context to ParsedCV (same logic as original CVParser.parse())
            
            # Contact and name (from EntityExtractor)
            result.contact = context.entities.get('contact', ContactInfo())
            result.name = context.entities.get('name')
            
            # Summary (from EntityExtractor)
            result.summary = context.entities.get('summary')
            
            # Skills (from SkillNormalizer)
            result.skills = context.skills
            
            # Experience (from ExperienceExtractor)
            result.experience = context.experiences
            
            # Education (from EducationExtractor)
            result.education = context.education
            
            # Step 8: Calculate total experience (same logic as CVParser._calculate_total_experience())
            result.total_experience_years = self._calculate_total_experience(
                result.experience
            )
            
            # Step 9: Extract languages (same logic as CVParser._extract_languages())
            if 'languages' in context.sections:
                result.languages = self._extract_languages(context.sections['languages'])
            
            # Step 10: Calculate extraction confidence (same logic as CVParser._calculate_confidence())
            result.extraction_confidence = self._calculate_confidence(result)
            
            # Add any warnings from pipeline stages
            result.parsing_warnings.extend(context.warnings)
            
        except Exception as e:
            result.parsing_warnings.append(f"Parsing error: {str(e)}")
            result.extraction_confidence = 0.0
        
        return result
    
    def _calculate_total_experience(self, experiences: List) -> Optional[float]:
        """
        Calculate total years of experience.
        
        This method is IDENTICAL to CVParser._calculate_total_experience()
        """
        total_months = 0
        
        for exp in experiences:
            if exp.duration_months:
                total_months += exp.duration_months
        
        if total_months > 0:
            return round(total_months / 12, 1)
        
        return None
    
    def _extract_languages(self, text: str) -> List[str]:
        """
        Extract languages from languages section.
        
        This method is IDENTICAL to CVParser._extract_languages()
        """
        languages = []
        
        text_lower = text.lower()
        
        for lang in KNOWN_LANGUAGES:
            if lang in text_lower:
                languages.append(lang.title())
        
        return languages
    
    def _calculate_confidence(self, result: ParsedCV) -> float:
        """
        Calculate overall extraction confidence score.
        Based on how many fields were successfully extracted.
        
        This method is IDENTICAL to CVParser._calculate_confidence()
        """
        score = 0.0
        max_score = 0.0
        
        # Name (important)
        max_score += 15
        if result.name:
            score += 15
        
        # Contact (important)
        max_score += 15
        if result.contact.email:
            score += 10
        if result.contact.phone:
            score += 5
        
        # Skills (very important)
        max_score += 25
        if result.skills:
            score += min(25, len(result.skills) * 3)
        
        # Experience (very important)
        max_score += 25
        if result.experience:
            score += min(25, len(result.experience) * 8)
        
        # Education
        max_score += 15
        if result.education:
            score += min(15, len(result.education) * 8)
        
        # Summary
        max_score += 5
        if result.summary:
            score += 5
        
        return round(min(score / max_score, 1.0), 2) if max_score > 0 else 0.0
    
    def parse_file(self, file_path: str) -> ParsedCV:
        """
        Parse CV from a file.
        Supports .txt files directly, .pdf and .docx require additional processing.
        
        This method is IDENTICAL to CVParser.parse_file()
        
        Args:
            file_path: Path to CV file
            
        Returns:
            ParsedCV object
        """
        path = Path(file_path)
        
        if not path.exists():
            result = ParsedCV(raw_text="")
            result.parsing_warnings.append(f"File not found: {file_path}")
            return result
        
        ext = path.suffix.lower()
        
        if ext == '.txt':
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.parse(text)
        
        elif ext == '.pdf':
            # PDF parsing would require PyPDF2 or pdfplumber
            # For now, return error
            result = ParsedCV(raw_text="")
            result.parsing_warnings.append(
                "PDF parsing not yet implemented. Please provide extracted text."
            )
            return result
        
        elif ext in ['.docx', '.doc']:
            # DOCX parsing would require python-docx
            result = ParsedCV(raw_text="")
            result.parsing_warnings.append(
                "DOCX parsing not yet implemented. Please provide extracted text."
            )
            return result
        
        else:
            result = ParsedCV(raw_text="")
            result.parsing_warnings.append(f"Unsupported file format: {ext}")
            return result
