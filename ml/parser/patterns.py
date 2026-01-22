"""
Regex Patterns for CV Parsing

This module centralizes ALL regex patterns used for CV parsing.
NO regex literals should appear in stage logic - all patterns defined here.

Patterns are organized by category:
- Contact information (email, phone, LinkedIn)
- Dates and time ranges
- Education degrees
- Job titles and company names
- Section headers

All patterns are pre-compiled for performance.
"""

import re
from typing import Dict, List, Pattern


# =============================================================================
# CONTACT INFORMATION PATTERNS
# =============================================================================

EMAIL_PATTERN: Pattern = re.compile(
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    re.IGNORECASE
)

PHONE_PATTERNS: List[Pattern] = [
    re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
    re.compile(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'),  # US format
    re.compile(r'\b\d{10,12}\b'),  # Simple 10-12 digit numbers
]

LINKEDIN_PATTERN: Pattern = re.compile(
    r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?',
    re.IGNORECASE
)


# =============================================================================
# DATE AND TIME RANGE PATTERNS
# =============================================================================

DATE_PATTERNS: List[Pattern] = [
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

YEAR_PATTERN: Pattern = re.compile(r'\b(19|20)\d{2}\b')


# =============================================================================
# EDUCATION DEGREE PATTERNS
# =============================================================================

DEGREE_PATTERNS: Dict[str, Pattern] = {
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


# =============================================================================
# JOB TITLE AND COMPANY PATTERNS
# =============================================================================

# Common job title keywords (used for detection)
JOB_TITLE_KEYWORDS: List[str] = [
    'engineer', 'developer', 'manager', 'director', 'analyst', 'consultant',
    'coordinator', 'specialist', 'executive', 'officer', 'lead', 'head',
    'supervisor', 'administrator', 'assistant', 'associate', 'senior',
    'junior', 'principal', 'architect', 'designer', 'scientist', 'intern',
    # Logistics specific
    'logistics', 'supply chain', 'warehouse', 'transportation', 'procurement',
    'operations', 'freight', 'shipping', 'inventory', 'distribution',
]

# Common company suffixes (for company name detection)
COMPANY_SUFFIXES: List[str] = [
    'inc', 'inc.', 'corp', 'corp.', 'corporation', 'llc', 'ltd', 'ltd.',
    'limited', 'pvt', 'private', 'co', 'co.', 'company', 'group',
    'technologies', 'solutions', 'services', 'consulting', 'systems',
]


# =============================================================================
# SECTION HEADER PATTERNS
# =============================================================================

# Pattern for detecting section headers (typically ALL CAPS or Title Case)
HEADER_PATTERN: Pattern = re.compile(
    r'^[\s]*([A-Z][A-Za-z\s&/]+)[\s]*[:\-–—]*[\s]*$',
    re.MULTILINE
)

# Section keywords organized by category
SECTION_KEYWORDS: Dict[str, List[str]] = {
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


# =============================================================================
# SKILL EXTRACTION PATTERNS
# =============================================================================

# Pattern for skill lists (bullet points, "Skills:" sections, etc.)
SKILL_LIST_PATTERN: Pattern = re.compile(
    r'(?:^|\n)\s*[-•*]\s*([^:\n]+?)(?:\n|$)|'  # Bullet points
    r'(?:skills?|technologies?|tools?)[\s:]+([^.\n]+)',  # After "skills:"
    re.IGNORECASE
)


# =============================================================================
# LANGUAGE PATTERNS
# =============================================================================

# Known language names (for language extraction)
KNOWN_LANGUAGES: List[str] = [
    'english', 'arabic', 'hindi', 'urdu', 'french', 'spanish',
    'german', 'mandarin', 'chinese', 'japanese', 'korean',
    'portuguese', 'russian', 'italian', 'dutch', 'tamil',
    'telugu', 'malayalam', 'bengali', 'punjabi', 'marathi',
    'gujarati', 'kannada', 'tagalog', 'thai', 'vietnamese',
]


# =============================================================================
# EXTRACTION FUNCTIONS
# =============================================================================

def extract_emails(text: str) -> List[str]:
    """Extract all email addresses from text."""
    return list(set(EMAIL_PATTERN.findall(text)))


def extract_phones(text: str) -> List[str]:
    """Extract all phone numbers from text."""
    phones = []
    for pattern in PHONE_PATTERNS:
        matches = pattern.findall(text)
        for match in matches:
            # Clean and validate
            cleaned = re.sub(r'[^\d+]', '', match)
            if 7 <= len(cleaned) <= 15:  # Valid phone length
                phones.append(match.strip())
    return list(set(phones))[:2]  # Return max 2 phone numbers


def extract_linkedin(text: str) -> str:
    """Extract LinkedIn URL from text."""
    match = LINKEDIN_PATTERN.search(text)
    return match.group(0) if match else None


def extract_date_ranges(text: str) -> List[Dict]:
    """Extract date ranges from text (for experience/education)."""
    date_ranges = []
    
    for pattern in DATE_PATTERNS:
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


def extract_years(text: str) -> List[int]:
    """Extract all 4-digit years from text."""
    matches = YEAR_PATTERN.findall(text)
    return sorted([int(f"{prefix}{suffix}") 
                  for prefix, suffix in [(m[:2], m[2:]) for m in 
                                         [YEAR_PATTERN.search(text).group() 
                                          for _ in range(len(matches))]]]
                  if matches else [])


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def is_likely_job_title(text: str) -> bool:
    """Check if text looks like a job title using keyword matching."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in JOB_TITLE_KEYWORDS)


def is_likely_company_name(text: str) -> bool:
    """Check if text looks like a company name using suffix matching."""
    text_lower = text.lower()
    words = text_lower.split()
    
    # Check if any word is a company suffix
    for word in words:
        word_clean = word.rstrip('.,')
        if word_clean in COMPANY_SUFFIXES:
            return True
    
    return False


def detect_degree_level(text: str) -> str:
    """Detect the highest degree level mentioned in text."""
    for level, pattern in DEGREE_PATTERNS.items():
        if pattern.search(text):
            return level
    return None

