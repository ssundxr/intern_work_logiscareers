"""
SectionSegmenter Stage

Segments CV text into logical sections (header, summary, experience, education, etc.)

This stage extracts the SectionDetector logic from the original cv_parser.py
and adapts it to the pipeline architecture. ALL section detection logic is
preserved exactly.

Section Detection Strategy:
1. Keyword matching (exact/substring)
2. Semantic similarity (if embedding model available)
3. Line-by-line scanning with header detection
"""

from typing import Dict, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from ..embedding_model import EmbeddingModel
from .pipeline import ParserStage, ParsingContext, ParsingStageError
from .patterns import SECTION_KEYWORDS, HEADER_PATTERN


class SectionSegmenter(ParserStage):
    """
    Second stage in the parsing pipeline - segments CV into sections.
    
    This stage identifies CV sections (summary, experience, education, etc.)
    using keyword matching and optional semantic similarity.
    
    The logic is extracted directly from the original SectionDetector class
    with NO modifications to preserve exact behavior.
    """
    
    def __init__(self):
        self._embedding_model = None
        self._section_embeddings = None
        self._keyword_to_section = None
    
    @property
    def name(self) -> str:
        return "SectionSegmenter"
    
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
            
            for section, keywords in SECTION_KEYWORDS.items():
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
        
        This method is IDENTICAL to SectionDetector.detect_section()
        """
        header_clean = header_text.strip().lower()
        
        # First try exact/substring matching
        for section, keywords in SECTION_KEYWORDS.items():
            for kw in keywords:
                if kw in header_clean or header_clean in kw:
                    return section, 1.0
        
        # Try semantic matching if available
        if NUMPY_AVAILABLE:
            try:
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
        
        This method is IDENTICAL to SectionDetector.segment_cv()
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
    
    def process(self, context: ParsingContext) -> None:
        """
        Segment CV text into sections.
        
        Args:
            context: Parsing context with cleaned_text
            
        Updates:
            context.sections: Dict mapping section names to content
            
        Raises:
            ParsingStageError: If segmentation fails
        """
        try:
            text = context.cleaned_text
            
            if not text:
                raise ParsingStageError(
                    self.name,
                    "No cleaned text available for segmentation"
                )
            
            # Segment CV using original logic
            sections = self.segment_cv(text)
            
            if not sections:
                context.add_warning(self.name, "No sections detected in CV")
            
            context.sections = sections
            context.set_metadata(self.name, "section_count", len(sections))
            context.set_metadata(self.name, "section_names", list(sections.keys()))
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Section segmentation failed: {str(e)}",
                original_exception=e
            )
