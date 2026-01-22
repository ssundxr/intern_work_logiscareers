"""
EducationExtractor Stage

Extracts structured education information from CV text.

This stage extracts the EducationExtractor logic from the original cv_parser.py
and adapts it to the pipeline architecture. ALL extraction logic is preserved exactly.

Extracted Information:
- Degree levels (PhD, Masters, Bachelors, Diploma)
- Institutions/Universities
- Fields of study
- Graduation years
"""

import re
from typing import List

from ..cv_parser import ParsedEducation
from .pipeline import ParserStage, ParsingContext, ParsingStageError
from .patterns import detect_degree_level


class EducationExtractor(ParserStage):
    """
    Sixth stage in the parsing pipeline - extracts education information.
    
    This stage extracts:
    - Degree levels
    - Institutions/universities
    - Fields of study
    - Graduation years
    
    The logic is extracted directly from the original EducationExtractor class
    with NO modifications to preserve exact behavior.
    """
    
    # Common university keywords
    UNIVERSITY_KEYWORDS = [
        'university', 'college', 'institute', 'school', 'academy',
        'polytechnic', 'iit', 'mit', 'stanford', 'harvard', 'oxford',
    ]
    
    # Common fields of study
    FIELDS_OF_STUDY = [
        'computer science', 'information technology', 'engineering',
        'business administration', 'management', 'economics', 'finance',
        'mathematics', 'physics', 'chemistry', 'biology', 'commerce',
        'logistics', 'supply chain', 'operations', 'data science',
        'artificial intelligence', 'machine learning', 'electrical',
        'mechanical', 'civil', 'chemical', 'software',
    ]
    
    @property
    def name(self) -> str:
        return "EducationExtractor"
    
    def extract_education(self, text: str) -> List[ParsedEducation]:
        """
        Extract education entries from text.
        
        This method is IDENTICAL to EducationExtractor.extract_education()
        """
        education = []
        lines = text.split('\n')
        
        current_edu = None
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Check for degree
            degree_level = detect_degree_level(stripped)
            
            if degree_level:
                if current_edu:
                    education.append(current_edu)
                
                current_edu = ParsedEducation(degree=degree_level)
                
                # Try to extract field of study
                for field in self.FIELDS_OF_STUDY:
                    if field.lower() in stripped.lower():
                        current_edu.field_of_study = field.title()
                        break
                
                # Extract year
                year_match = re.search(r'\b(19|20)\d{2}\b', stripped)
                if year_match:
                    current_edu.graduation_year = int(year_match.group())
                
                continue
            
            # Check for university
            if current_edu and any(kw in stripped.lower() for kw in self.UNIVERSITY_KEYWORDS):
                current_edu.institution = stripped
                continue
            
            # Check for year only
            if current_edu:
                year_match = re.search(r'\b(19|20)\d{2}\b', stripped)
                if year_match and not current_edu.graduation_year:
                    current_edu.graduation_year = int(year_match.group())
        
        if current_edu:
            education.append(current_edu)
        
        return education
    
    def process(self, context: ParsingContext) -> None:
        """
        Extract education from CV sections.
        
        Args:
            context: Parsing context with sections
            
        Updates:
            context.education: List of ParsedEducation objects
            
        Raises:
            ParsingStageError: If education extraction fails
        """
        try:
            sections = context.sections
            
            if not sections:
                context.add_warning(self.name, "No sections available for education extraction")
                return
            
            # Extract education (same logic as CVParser.parse())
            if 'education' in sections:
                education = self.extract_education(sections['education'])
                context.education = education
                context.set_metadata(self.name, "education_count", len(education))
            else:
                context.add_warning(self.name, "No education section found")
                context.education = []
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Education extraction failed: {str(e)}",
                original_exception=e
            )
