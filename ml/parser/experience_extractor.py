"""
ExperienceExtractor Stage

Extracts structured work experience from CV text.

This stage extracts the ExperienceExtractor logic from the original cv_parser.py
and adapts it to the pipeline architecture. ALL extraction logic is preserved exactly.

Extracted Information:
- Job titles
- Company names
- Date ranges (start/end dates)
- Duration in months
- Responsibilities
"""

import re
from datetime import datetime
from typing import List, Optional

from ..cv_parser import ParsedExperience
from .pipeline import ParserStage, ParsingContext, ParsingStageError
from .patterns import (
    extract_date_ranges,
    is_likely_job_title,
    COMPANY_SUFFIXES,
)


class ExperienceExtractor(ParserStage):
    """
    Fifth stage in the parsing pipeline - extracts work experience.
    
    This stage extracts:
    - Job titles
    - Company names
    - Employment dates and duration
    - Responsibilities
    
    The logic is extracted directly from the original ExperienceExtractor class
    with NO modifications to preserve exact behavior.
    """
    
    @property
    def name(self) -> str:
        return "ExperienceExtractor"
    
    def extract_experiences(self, text: str) -> List[ParsedExperience]:
        """
        Extract work experiences from text.
        
        This method is IDENTICAL to ExperienceExtractor.extract_experiences()
        """
        experiences = []
        
        # Split into potential experience blocks
        # Look for patterns: date range followed by job title/company
        date_ranges = extract_date_ranges(text)
        
        if not date_ranges:
            # Try to extract based on structure
            return self._extract_unstructured(text)
        
        lines = text.split('\n')
        current_exp = None
        current_responsibilities = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Check if this line contains a date range
            has_date = any(dr['raw'] in line for dr in date_ranges)
            
            if has_date or is_likely_job_title(stripped):
                # Save previous experience
                if current_exp:
                    if current_responsibilities:
                        current_exp.responsibilities = '\n'.join(current_responsibilities)
                    experiences.append(current_exp)
                
                current_exp = ParsedExperience()
                current_responsibilities = []
                
                # Try to extract job title and company
                self._parse_experience_header(stripped, current_exp)
                
                # Extract date range
                for dr in date_ranges:
                    if dr['raw'] in line:
                        current_exp.start_date = dr.get('start') or dr.get('start_year')
                        end = dr.get('end') or dr.get('end_year')
                        
                        if end and end.lower() in ['present', 'current']:
                            current_exp.is_current = True
                            current_exp.end_date = 'Present'
                        else:
                            current_exp.end_date = end
                        
                        # Calculate duration
                        current_exp.duration_months = self._calculate_duration(
                            current_exp.start_date, 
                            current_exp.end_date
                        )
                        break
            
            elif current_exp and (stripped.startswith('-') or stripped.startswith('•')):
                # This is likely a responsibility bullet point
                current_responsibilities.append(stripped.lstrip('-•* '))
        
        # Save last experience
        if current_exp:
            if current_responsibilities:
                current_exp.responsibilities = '\n'.join(current_responsibilities)
            experiences.append(current_exp)
        
        return experiences
    
    def _extract_unstructured(self, text: str) -> List[ParsedExperience]:
        """
        Extract experiences from unstructured text.
        
        This method is IDENTICAL to ExperienceExtractor._extract_unstructured()
        """
        experiences = []
        
        # Look for job-title-like lines
        for line in text.split('\n'):
            stripped = line.strip()
            
            if is_likely_job_title(stripped) and len(stripped) < 100:
                exp = ParsedExperience(job_title=stripped)
                experiences.append(exp)
        
        return experiences[:5]  # Limit to 5 experiences
    
    def _parse_experience_header(self, text: str, exp: ParsedExperience):
        """
        Parse job title and company from experience header line.
        
        This method is IDENTICAL to ExperienceExtractor._parse_experience_header()
        """
        # Common patterns:
        # "Software Engineer at Google"
        # "Software Engineer, Google Inc."
        # "Google | Software Engineer"
        
        # Try "at" separator
        if ' at ' in text.lower():
            parts = re.split(r'\s+at\s+', text, flags=re.IGNORECASE)
            if len(parts) >= 2:
                exp.job_title = parts[0].strip()
                exp.company_name = parts[1].strip()
                return
        
        # Try pipe separator
        if '|' in text:
            parts = text.split('|')
            if len(parts) >= 2:
                # Determine which is title vs company
                for i, part in enumerate(parts):
                    part_clean = part.strip()
                    if is_likely_job_title(part_clean):
                        exp.job_title = part_clean
                    elif any(suffix in part_clean.lower() for suffix in COMPANY_SUFFIXES):
                        exp.company_name = part_clean
                return
        
        # Try comma separator
        if ',' in text:
            parts = text.split(',')
            if len(parts) >= 2:
                exp.job_title = parts[0].strip()
                exp.company_name = parts[1].strip()
                return
        
        # Default: assume it's a job title
        if is_likely_job_title(text):
            exp.job_title = text
    
    def _calculate_duration(
        self, 
        start: Optional[str], 
        end: Optional[str]
    ) -> Optional[int]:
        """
        Calculate duration in months between start and end dates.
        
        This method is IDENTICAL to ExperienceExtractor._calculate_duration()
        """
        if not start:
            return None
        
        try:
            # Parse start year
            start_year = int(re.search(r'\d{4}', start).group())
            start_month = 1
            
            # Try to get month
            month_match = re.search(
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', 
                start, 
                re.IGNORECASE
            )
            if month_match:
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                start_month = months.index(month_match.group().lower()[:3]) + 1
            
            # Parse end
            if not end or end.lower() in ['present', 'current']:
                end_year = datetime.now().year
                end_month = datetime.now().month
            else:
                end_year = int(re.search(r'\d{4}', end).group())
                end_month = 12
                
                month_match = re.search(
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', 
                    end, 
                    re.IGNORECASE
                )
                if month_match:
                    months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                             'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                    end_month = months.index(month_match.group().lower()[:3]) + 1
            
            # Calculate months
            return (end_year - start_year) * 12 + (end_month - start_month)
        
        except Exception:
            return None
    
    def process(self, context: ParsingContext) -> None:
        """
        Extract work experience from CV sections.
        
        Args:
            context: Parsing context with sections
            
        Updates:
            context.experiences: List of ParsedExperience objects
            
        Raises:
            ParsingStageError: If experience extraction fails
        """
        try:
            sections = context.sections
            
            if not sections:
                context.add_warning(self.name, "No sections available for experience extraction")
                return
            
            # Extract experience (same logic as CVParser.parse())
            if 'experience' in sections:
                experiences = self.extract_experiences(sections['experience'])
                context.experiences = experiences
                context.set_metadata(self.name, "experience_count", len(experiences))
            else:
                context.add_warning(self.name, "No experience section found")
                context.experiences = []
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Experience extraction failed: {str(e)}",
                original_exception=e
            )
