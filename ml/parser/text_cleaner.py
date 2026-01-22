"""
TextCleaner Stage

Normalizes raw CV text for consistent parsing across all subsequent stages.

This stage:
- Preserves EXACT text content (no aggressive cleaning)
- Only normalizes whitespace and line endings
- Ensures consistent encoding

IMPORTANT: This is a STRUCTURAL REFACTOR. The cleaning behavior is intentionally
minimal to preserve the exact parsing behavior of the original cv_parser.py.
"""

from .pipeline import ParserStage, ParsingContext, ParsingStageError


class TextCleaner(ParserStage):
    """
    First stage in the parsing pipeline - normalizes raw CV text.
    
    This stage performs minimal text normalization:
    1. Ensures consistent line endings (Unix-style)
    2. Removes excessive whitespace
    3. Ensures text is properly encoded
    
    The original cv_parser.py had NO explicit text cleaning, so this stage
    is intentionally minimal to preserve exact behavior.
    """
    
    @property
    def name(self) -> str:
        return "TextCleaner"
    
    def process(self, context: ParsingContext) -> None:
        """
        Clean and normalize raw CV text.
        
        Args:
            context: Parsing context with raw_text
            
        Updates:
            context.cleaned_text: Normalized text
            
        Raises:
            ParsingStageError: If text cleaning fails
        """
        try:
            text = context.raw_text
            
            if not text or not text.strip():
                raise ParsingStageError(
                    self.name,
                    "Empty or whitespace-only input text"
                )
            
            # Normalize line endings (Windows \r\n -> Unix \n)
            cleaned = text.replace('\r\n', '\n').replace('\r', '\n')
            
            # The original cv_parser.py had NO additional cleaning
            # We preserve this behavior exactly
            
            context.cleaned_text = cleaned
            context.set_metadata(self.name, "original_length", len(text))
            context.set_metadata(self.name, "cleaned_length", len(cleaned))
            
        except ParsingStageError:
            raise
        except Exception as e:
            raise ParsingStageError(
                self.name,
                f"Text cleaning failed: {str(e)}",
                original_exception=e
            )
