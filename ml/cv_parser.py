# Advanced NER-based CV Parser for Logis Career
# ml/cv_parser.py
# 
# This module implements a production-grade CV parsing system using:
# - Regex-based pattern matching for structured data (emails, phones, dates)
# - Rule-based NER with skill taxonomy integration
# - Semantic section detection using sentence embeddings
# - Multi-stage pipeline architecture for robust extraction

import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path

import yaml

# Import our embedding model for semantic matching
from logis_ai_candidate_engine.ml.embedding_model import EmbeddingModel


# =============================================================================
# DATA CLASSES FOR PARSED CV STRUCTURE
# =============================================================================

@dataclass
class ContactInfo:
    """Extracted contact information from CV"""
    email: Optional[str] = None
    phone: Optional[str] = None
    alternative_phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ParsedExperience:
    """Structured work experience entry"""
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    is_current: bool = False
    responsibilities: Optional[str] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ParsedEducation:
    """Structured education entry"""
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    institution: Optional[str] = None
    graduation_year: Optional[int] = None
    location: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class ParsedCertification:
    """Structured certification entry"""
    name: str
    issuer: Optional[str] = None
    year: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class SkillExtraction:
    """Result of skill extraction with confidence"""
    skill: str
    normalized_skill: str
    confidence: float
    source_section: str  # Which section of CV this was found in
    
    def to_dict(self) -> Dict:
        return self.__dict__.copy()


@dataclass
class ParsedCV:
    """Complete parsed CV structure"""
    raw_text: str
    name: Optional[str] = None
    contact: ContactInfo = field(default_factory=ContactInfo)
    summary: Optional[str] = None
    skills: List[SkillExtraction] = field(default_factory=list)
    experience: List[ParsedExperience] = field(default_factory=list)
    education: List[ParsedEducation] = field(default_factory=list)
    certifications: List[ParsedCertification] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    total_experience_years: Optional[float] = None
    extraction_confidence: float = 0.0
    parsing_warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "contact": self.contact.to_dict(),
            "summary": self.summary,
            "skills": [s.to_dict() for s in self.skills],
            "experience": [e.to_dict() for e in self.experience],
            "education": [e.to_dict() for e in self.education],
            "certifications": [c.to_dict() for c in self.certifications],
            "languages": self.languages,
            "total_experience_years": self.total_experience_years,
            "extraction_confidence": self.extraction_confidence,
            "parsing_warnings": self.parsing_warnings,
        }


# =============================================================================
# PATTERN MATCHERS - Regex-based extraction for structured data
# =============================================================================

class PatternMatcher:
    """
    Regex-based pattern matcher for structured data extraction.
    Handles emails, phones, dates, URLs, and other structured patterns.
    """
    
    # Email patterns
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )
    
    # Phone patterns (international and local formats)
    PHONE_PATTERNS = [
        re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
        re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # US format
        re.compile(r'\b\d{10,12}\b'),  # Simple 10-12 digit numbers
    ]
    
    # LinkedIn URL pattern
    LINKEDIN_PATTERN = re.compile(
        r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?',
        re.IGNORECASE
    )
    
    # Date patterns for experience/education
    DATE_PATTERNS = [
        # Month Year - Month Year (e.g., "Jan 2020 - Dec 2023")
        re.compile(
            r'(?P<start_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*'
            r'(?P<start_year>\d{4})\s*[-–—to]+\s*'
            r'(?P<end_month>Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
            r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|Present|Current)\s*'
            r'(?P<end_year>\d{4})?',
            re.IGNORECASE
        ),
        # MM/YYYY - MM/YYYY format
        re.compile(
            r'(?P<start>\d{1,2}/\d{4})\s*[-–—to]+\s*(?P<end>\d{1,2}/\d{4}|Present|Current)',
            re.IGNORECASE
        ),
        # YYYY - YYYY format
        re.compile(
            r'(?P<start_year>\d{4})\s*[-–—to]+\s*(?P<end_year>\d{4}|Present|Current)',
            re.IGNORECASE
        ),
    ]
    
    # Year pattern for education
    YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}\b')
    
    # Degree patterns
    DEGREE_PATTERNS = {
        'phd': re.compile(r'\b(?:Ph\.?D\.?|Doctor(?:ate)?|D\.Phil)\b', re.IGNORECASE),
        'masters': re.compile(
            r'\b(?:M\.?S\.?|M\.?Sc\.?|M\.?A\.?|MBA|M\.?Tech|M\.?E\.?|Master(?:\'?s)?)\b',
            re.IGNORECASE
        ),
        'bachelors': re.compile(
            r'\b(?:B\.?S\.?|B\.?Sc\.?|B\.?A\.?|B\.?Tech|B\.?E\.?|Bachelor(?:\'?s)?|'
            r'B\.?Com|BBA|Undergraduate)\b',
            re.IGNORECASE
        ),
        'diploma': re.compile(r'\b(?:Diploma|Associate|Certificate)\b', re.IGNORECASE),
    }
    
    # Common job title patterns
    JOB_TITLE_KEYWORDS = [
        'engineer', 'developer', 'manager', 'director', 'analyst', 'consultant',
        'coordinator', 'specialist', 'executive', 'officer', 'lead', 'head',
        'supervisor', 'administrator', 'assistant', 'associate', 'senior',
        'junior', 'principal', 'architect', 'designer', 'scientist', 'intern',
        # Logistics specific
        'logistics', 'supply chain', 'warehouse', 'transportation', 'procurement',
        'operations', 'freight', 'shipping', 'inventory', 'distribution',
    ]
    
    @classmethod
    def extract_emails(cls, text: str) -> List[str]:
        """Extract all email addresses from text"""
        return list(set(cls.EMAIL_PATTERN.findall(text)))
    
    @classmethod
    def extract_phones(cls, text: str) -> List[str]:
        """Extract all phone numbers from text"""
        phones = []
        for pattern in cls.PHONE_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                # Clean and validate
                cleaned = re.sub(r'[^\d+]', '', match)
                if 7 <= len(cleaned) <= 15:  # Valid phone length
                    phones.append(match.strip())
        return list(set(phones))[:2]  # Return max 2 phone numbers
    
    @classmethod
    def extract_linkedin(cls, text: str) -> Optional[str]:
        """Extract LinkedIn URL from text"""
        match = cls.LINKEDIN_PATTERN.search(text)
        return match.group(0) if match else None
    
    @classmethod
    def extract_date_ranges(cls, text: str) -> List[Dict]:
        """Extract date ranges from text (for experience/education)"""
        date_ranges = []
        
        for pattern in cls.DATE_PATTERNS:
            for match in pattern.finditer(text):
                groups = match.groupdict()
                date_ranges.append({
                    'raw': match.group(0),
                    'start': groups.get('start') or groups.get('start_year'),
                    'end': groups.get('end') or groups.get('end_year') or groups.get('end_month'),
                    'start_month': groups.get('start_month'),
                    'end_month': groups.get('end_month'),
                    'start_year': groups.get('start_year'),
                    'end_year': groups.get('end_year'),
                })
        
        return date_ranges
    
    @classmethod
    def extract_years(cls, text: str) -> List[int]:
        """Extract all 4-digit years from text"""
        matches = cls.YEAR_PATTERN.findall(text)
        return sorted([int(f"{prefix}{suffix}") 
                      for prefix, suffix in [(m[:2], m[2:]) for m in 
                                             [cls.YEAR_PATTERN.search(text).group() 
                                              for _ in range(len(matches))]]]
                      if matches else [])
    
    @classmethod
    def detect_degree_level(cls, text: str) -> Optional[str]:
        """Detect the highest degree level mentioned in text"""
        for level, pattern in cls.DEGREE_PATTERNS.items():
            if pattern.search(text):
                return level
        return None
    
    @classmethod
    def is_likely_job_title(cls, text: str) -> bool:
        """Check if text looks like a job title"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.JOB_TITLE_KEYWORDS)


# =============================================================================
# SECTION DETECTOR - Identifies CV sections using keywords and semantics
# =============================================================================

class SectionDetector:
    """
    Detects and segments CV sections using keyword matching
    and semantic similarity with section headers.
    """
    
    # Section header keywords (normalized)
    SECTION_KEYWORDS = {
        'summary': [
            'summary', 'profile', 'objective', 'about', 'overview', 
            'professional summary', 'career objective', 'about me',
        ],
        'experience': [
            'experience', 'work history', 'employment', 'professional experience',
            'work experience', 'career history', 'positions held',
        ],
        'education': [
            'education', 'academic', 'qualifications', 'educational background',
            'academic background', 'degrees', 'schooling',
        ],
        'skills': [
            'skills', 'technical skills', 'competencies', 'expertise',
            'core competencies', 'key skills', 'proficiencies', 'technologies',
        ],
        'certifications': [
            'certifications', 'certificates', 'licenses', 'credentials',
            'professional certifications', 'training',
        ],
        'languages': [
            'languages', 'language skills', 'linguistic abilities',
        ],
        'projects': [
            'projects', 'key projects', 'notable projects', 'portfolio',
        ],
        'achievements': [
            'achievements', 'awards', 'honors', 'accomplishments',
            'recognition', 'publications',
        ],
    }
    
    # Patterns for section headers
    HEADER_PATTERN = re.compile(
        r'^[\s]*([A-Z][A-Za-z\s&/]+)[\s]*[:\-–—]*[\s]*$',
        re.MULTILINE
    )
    
    def __init__(self):
        self._embedding_model = None
        self._section_embeddings = None
    
    def _get_embedding_model(self):
        """Lazy load embedding model"""
        if self._embedding_model is None:
            try:
                self._embedding_model = EmbeddingModel.load()
            except Exception:
                self._embedding_model = None
        return self._embedding_model
    
    def _get_section_embeddings(self):
        """Get embeddings for section keywords (cached)"""
        if self._section_embeddings is None:
            all_keywords = []
            keyword_to_section = {}
            
            for section, keywords in self.SECTION_KEYWORDS.items():
                for kw in keywords:
                    all_keywords.append(kw)
                    keyword_to_section[kw] = section
            
            try:
                embeddings = EmbeddingModel.encode(all_keywords)
                self._section_embeddings = {
                    kw: emb for kw, emb in zip(all_keywords, embeddings)
                }
                self._keyword_to_section = keyword_to_section
            except Exception:
                self._section_embeddings = {}
                self._keyword_to_section = {}
        
        return self._section_embeddings, self._keyword_to_section
    
    def detect_section(self, header_text: str) -> Tuple[Optional[str], float]:
        """
        Detect which section a header belongs to.
        Returns (section_name, confidence_score)
        """
        header_clean = header_text.strip().lower()
        
        # First try exact/substring matching
        for section, keywords in self.SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in header_clean or header_clean in kw:
                    return section, 1.0
        
        # Try semantic matching if available
        try:
            import numpy as np
            section_embeddings, keyword_to_section = self._get_section_embeddings()
            
            if section_embeddings:
                header_embedding = EmbeddingModel.encode([header_text])[0]
                
                best_match = None
                best_score = 0.0
                
                for kw, kw_embedding in section_embeddings.items():
                    similarity = float(np.dot(header_embedding, kw_embedding))
                    if similarity > best_score:
                        best_score = similarity
                        best_match = keyword_to_section.get(kw)
                
                if best_score >= 0.6:  # Threshold for semantic match
                    return best_match, best_score
        except Exception:
            pass
        
        return None, 0.0
    
    def segment_cv(self, text: str) -> Dict[str, str]:
        """
        Segment CV text into sections.
        Returns dict mapping section names to their content.
        """
        sections = {}
        lines = text.split('\n')
        
        current_section = 'header'  # First part is typically name/contact
        current_content = []
        
        for line in lines:
            # Check if this line looks like a section header
            stripped = line.strip()
            
            if stripped and len(stripped) < 50:  # Headers are typically short
                section, confidence = self.detect_section(stripped)
                
                if section and confidence >= 0.6:
                    # Save previous section
                    if current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    current_section = section
                    current_content = []
                    continue
            
            current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections


# =============================================================================
# SKILL EXTRACTOR - Uses taxonomy for intelligent skill extraction
# =============================================================================

class SkillExtractor:
    """
    Extracts skills from CV text using the skill taxonomy.
    Performs both exact matching and fuzzy/semantic matching.
    """
    
    _taxonomy: Optional[Dict] = None
    _all_skills: Optional[Set[str]] = None
    
    @classmethod
    def _load_taxonomy(cls) -> Dict:
        """Load skill taxonomy from YAML file"""
        if cls._taxonomy is None:
            taxonomy_path = Path(__file__).parent.parent / 'config' / 'skills_taxonomy.yaml'
            
            if taxonomy_path.exists():
                with open(taxonomy_path, 'r', encoding='utf-8') as f:
                    cls._taxonomy = yaml.safe_load(f)
            else:
                cls._taxonomy = {'synonyms': {}, 'categories': {}}
        
        return cls._taxonomy
    
    @classmethod
    def _get_all_skills(cls) -> Set[str]:
        """Get all known skills from taxonomy (including synonyms)"""
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
        """Normalize a skill string"""
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
        Extract skills from text using multiple strategies:
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


# =============================================================================
# EXPERIENCE EXTRACTOR - Extracts work history
# =============================================================================

class ExperienceExtractor:
    """
    Extracts structured work experience from CV text.
    Uses pattern matching and heuristics to identify:
    - Job titles
    - Company names
    - Date ranges
    - Responsibilities
    """
    
    # Common company suffixes
    COMPANY_SUFFIXES = [
        'inc', 'inc.', 'corp', 'corp.', 'corporation', 'llc', 'ltd', 'ltd.',
        'limited', 'pvt', 'private', 'co', 'co.', 'company', 'group',
        'technologies', 'solutions', 'services', 'consulting', 'systems',
    ]
    
    def extract_experiences(self, text: str) -> List[ParsedExperience]:
        """Extract work experiences from text"""
        experiences = []
        
        # Split into potential experience blocks
        # Look for patterns: date range followed by job title/company
        date_ranges = PatternMatcher.extract_date_ranges(text)
        
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
            
            if has_date or PatternMatcher.is_likely_job_title(stripped):
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
        """Extract experiences from unstructured text"""
        experiences = []
        
        # Look for job-title-like lines
        for line in text.split('\n'):
            stripped = line.strip()
            
            if PatternMatcher.is_likely_job_title(stripped) and len(stripped) < 100:
                exp = ParsedExperience(job_title=stripped)
                experiences.append(exp)
        
        return experiences[:5]  # Limit to 5 experiences
    
    def _parse_experience_header(self, text: str, exp: ParsedExperience):
        """Parse job title and company from experience header line"""
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
                    if PatternMatcher.is_likely_job_title(part_clean):
                        exp.job_title = part_clean
                    elif any(suffix in part_clean.lower() for suffix in self.COMPANY_SUFFIXES):
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
        if PatternMatcher.is_likely_job_title(text):
            exp.job_title = text
    
    def _calculate_duration(
        self, 
        start: Optional[str], 
        end: Optional[str]
    ) -> Optional[int]:
        """Calculate duration in months between start and end dates"""
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


# =============================================================================
# EDUCATION EXTRACTOR - Extracts educational background
# =============================================================================

class EducationExtractor:
    """
    Extracts structured education information from CV text.
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
    
    def extract_education(self, text: str) -> List[ParsedEducation]:
        """Extract education entries from text"""
        education = []
        lines = text.split('\n')
        
        current_edu = None
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                continue
            
            # Check for degree
            degree_level = PatternMatcher.detect_degree_level(stripped)
            
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


# =============================================================================
# MAIN CV PARSER - Orchestrates all extraction components
# =============================================================================

class CVParser:
    """
    Main CV parser class that orchestrates all extraction components.
    Provides a unified interface for parsing CVs from text or files.
    
    Usage:
        parser = CVParser()
        result = parser.parse(cv_text)
        
        # Access parsed data
        print(result.name)
        print(result.skills)
        print(result.experience)
    """
    
    def __init__(self):
        self.section_detector = SectionDetector()
        self.skill_extractor = SkillExtractor()
        self.experience_extractor = ExperienceExtractor()
        self.education_extractor = EducationExtractor()
    
    def parse(self, text: str) -> ParsedCV:
        """
        Parse CV text and extract all structured information.
        
        Args:
            text: Raw CV text content
            
        Returns:
            ParsedCV object containing all extracted information
        """
        result = ParsedCV(raw_text=text)
        
        try:
            # Step 1: Segment CV into sections
            sections = self.section_detector.segment_cv(text)
            
            # Step 2: Extract contact information (from header section)
            header_text = sections.get('header', text[:500])
            result.contact = self._extract_contact(header_text)
            
            # Step 3: Extract name (from header section)
            result.name = self._extract_name(header_text)
            
            # Step 4: Extract summary
            if 'summary' in sections:
                result.summary = sections['summary'][:500]  # Limit summary length
            
            # Step 5: Extract skills from all sections
            all_skills = []
            
            # Prioritize skills section
            if 'skills' in sections:
                all_skills.extend(
                    self.skill_extractor.extract_skills(sections['skills'], 'skills')
                )
            
            # Also check experience and summary for skills
            for section_name in ['experience', 'summary', 'header']:
                if section_name in sections:
                    section_skills = self.skill_extractor.extract_skills(
                        sections[section_name], section_name
                    )
                    # Only add if not already found
                    existing_normalized = {s.normalized_skill for s in all_skills}
                    for skill in section_skills:
                        if skill.normalized_skill not in existing_normalized:
                            all_skills.append(skill)
                            existing_normalized.add(skill.normalized_skill)
            
            result.skills = all_skills
            
            # Step 6: Extract experience
            if 'experience' in sections:
                result.experience = self.experience_extractor.extract_experiences(
                    sections['experience']
                )
            
            # Step 7: Extract education
            if 'education' in sections:
                result.education = self.education_extractor.extract_education(
                    sections['education']
                )
            
            # Step 8: Calculate total experience
            result.total_experience_years = self._calculate_total_experience(
                result.experience
            )
            
            # Step 9: Extract languages
            if 'languages' in sections:
                result.languages = self._extract_languages(sections['languages'])
            
            # Step 10: Calculate extraction confidence
            result.extraction_confidence = self._calculate_confidence(result)
            
        except Exception as e:
            result.parsing_warnings.append(f"Parsing error: {str(e)}")
            result.extraction_confidence = 0.0
        
        return result
    
    def _extract_contact(self, text: str) -> ContactInfo:
        """Extract contact information from header section"""
        contact = ContactInfo()
        
        # Extract email
        emails = PatternMatcher.extract_emails(text)
        if emails:
            contact.email = emails[0]
        
        # Extract phone(s)
        phones = PatternMatcher.extract_phones(text)
        if phones:
            contact.phone = phones[0]
            if len(phones) > 1:
                contact.alternative_phone = phones[1]
        
        # Extract LinkedIn
        contact.linkedin_url = PatternMatcher.extract_linkedin(text)
        
        return contact
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from header section"""
        lines = text.split('\n')
        
        for line in lines[:5]:  # Check first 5 lines
            stripped = line.strip()
            
            # Skip empty lines, emails, phones
            if not stripped:
                continue
            if '@' in stripped:
                continue
            if re.match(r'^[\d\+\-\(\)\s]+$', stripped):
                continue
            
            # Name is typically 2-4 words, title case
            words = stripped.split()
            if 2 <= len(words) <= 4:
                # Check if it looks like a name (starts with capital, no numbers)
                if all(w[0].isupper() for w in words if w) and not any(c.isdigit() for c in stripped):
                    return stripped
        
        return None
    
    def _calculate_total_experience(
        self, 
        experiences: List[ParsedExperience]
    ) -> Optional[float]:
        """Calculate total years of experience"""
        total_months = 0
        
        for exp in experiences:
            if exp.duration_months:
                total_months += exp.duration_months
        
        if total_months > 0:
            return round(total_months / 12, 1)
        
        return None
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract languages from languages section"""
        languages = []
        
        # Common language names
        known_languages = [
            'english', 'arabic', 'hindi', 'urdu', 'french', 'spanish',
            'german', 'mandarin', 'chinese', 'japanese', 'korean',
            'portuguese', 'russian', 'italian', 'dutch', 'tamil',
            'telugu', 'malayalam', 'bengali', 'punjabi', 'marathi',
            'gujarati', 'kannada', 'tagalog', 'thai', 'vietnamese',
        ]
        
        text_lower = text.lower()
        
        for lang in known_languages:
            if lang in text_lower:
                languages.append(lang.title())
        
        return languages
    
    def _calculate_confidence(self, result: ParsedCV) -> float:
        """
        Calculate overall extraction confidence score.
        Based on how many fields were successfully extracted.
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


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def parse_cv(text: str) -> ParsedCV:
    """
    Convenience function to parse CV text.
    
    Args:
        text: Raw CV text
        
    Returns:
        ParsedCV object with all extracted information
    """
    parser = CVParser()
    return parser.parse(text)


def parse_cv_file(file_path: str) -> ParsedCV:
    """
    Convenience function to parse CV from file.
    
    Args:
        file_path: Path to CV file
        
    Returns:
        ParsedCV object with all extracted information
    """
    parser = CVParser()
    return parser.parse_file(file_path)
