"""
EntityExtractor Stage

Extracts structured entities from CV text (contact info, name, summary)

This stage extracts the PatternMatcher logic and CVParser._extract_contact()
and _extract_name() methods from the original cv_parser.py. ALL extraction
logic is preserved exactly.

Extracted Entities:
- Contact Info (email, phone, LinkedIn)
- Name
- Summary
"""

import re
from typing import List, Optional

from ..cv_parser import ContactInfo
from .pipeline import ParserStage, ParsingContext, ParsingStageError
from .patterns import (
    EMAIL_PATTERN,
    PHONE_PATTERNS,
    LINKEDIN_PATTERN,
    extract_emails,
    extract_phones,
    extract_linkedin,
)


class EntityExtractor(ParserStage):
    """
    Third stage in the parsing pipeline - extracts structured entities.
    
    This stage extracts:
    - Contact information (email, phone, LinkedIn)
    - Candidate name
    - Professional summary
    
    The logic is extracted directly from the original PatternMatcher class
    and CVParser._extract_contact()/_extract_name() with NO modifications.
    """
    
    @property
    def name(self) -> str:
        return "EntityExtractor"
    
    def _extract_contact(self, text: str) -> ContactInfo:
        """
        Extract contact information from header section.
        
        This method is IDENTICAL to CVParser._extract_contact()
        """
        contact = ContactInfo()
        
        # Extract email
        emails = extract_emails(text)
        if emails:
            contact.email = emails[0]
        
        # Extract phone(s)
        phones = extract_phones(text)
        if phones:
            contact.phone = phones[0]
            if len(phones) > 1:
                contact.alternative_phone = phones[1]
        
        # Extract LinkedIn
        contact.linkedin_url = extract_linkedin(text)
        
        return contact
    
    def _extract_name(self, text: str) -> Optional[str]:
        """
        Extract candidate name from header section.
        
        This method is IDENTICAL to CVParser._extract_name()
        """
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
    
    def process(self, context: ParsingContext) -> None:
        """
        Extract entities from CV sections.
        
        Args:
            context: Parsing context with sections
            
        Updates:
            context.entities: Dict with 'contact', 'name', 'summary'
            
        Raises:
            ParsingStageError: If entity extraction fails
        """
        try:
            sections = context.sections
            
            if not sections:
                context.add_warning(self.name, "No sections available for entity extraction")
                return
            
            # Extract contact information (from header section)
            header_text = sections.get('header', context.cleaned_text[:500])
            contact = self._extract_contact(header_text)
            context.entities['contact'] = contact
            
            # Extract name (from header section)
            name = self._extract_name(header_text)
            context.entities['name'] = name
            
            if not name:
                context.add_warning(self.name, "Could not extract candidate name")
            
            # Extract summary
            if 'summary' in sections:
                summary = sections['summary'][:500]  # Limit summary length
                context.entities['summary'] = summary
            else:
                context.entities['summary'] = None
            
            context.set_metadata(self.name, "has_email", bool(contact.email))
            context.set_metadata(self.name, "has_phone", bool(contact.phone))
            context.set_metadata(self.name, "has_linkedin", bool(contact.linkedin_url))
            context.set_metadata(self.name, "has_name", bool(name))
            context.set_metadata(self.name, "has_summary", 'summary' in sections)
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Entity extraction failed: {str(e)}",
                original_exception=e
            )
