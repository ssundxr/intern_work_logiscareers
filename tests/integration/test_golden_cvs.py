"""
Golden CV Regression Tests

Tests CV parser against known-good CVs to prevent regressions.
Each golden CV has expected extraction results.

Author: Production Testing
Date: January 24, 2026
"""

import pytest
from pathlib import Path
from ml.cv_parser import CVParser


class TestGoldenCVRegression:
    """Regression tests using golden CV dataset"""
    
    @pytest.fixture
    def parser(self):
        """Create CV parser instance"""
        return CVParser()
    
    @pytest.fixture
    def golden_cv_dir(self):
        """Get path to golden CV directory"""
        return Path(__file__).parent.parent.parent / "data" / "golden_cvs"
    
    def test_golden_cv_1_logistics_manager(self, parser, golden_cv_dir):
        """Test parsing of golden CV 1 - Logistics Manager"""
        cv_path = golden_cv_dir / "golden_cv_1_logistics_manager.txt"
        
        if not cv_path.exists():
            pytest.skip(f"Golden CV not found: {cv_path}")
        
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        result = parser.parse(cv_text)
        
        # Assertions based on known content
        assert result.name is not None, "Should extract candidate name"
        assert result.contact.email is not None, "Should extract email"
        assert len(result.skills) > 0, "Should extract skills"
        assert len(result.experience) > 0, "Should extract work experience"
        assert result.total_experience_years is not None, "Should calculate total experience"
        
        # Logistics-specific expectations
        logistics_skills = [s.normalized_skill.lower() for s in result.skills]
        assert any('logistics' in skill or 'supply chain' in skill for skill in logistics_skills), \
            "Should detect logistics-related skills"
    
    def test_golden_cv_2_software_engineer(self, parser, golden_cv_dir):
        """Test parsing of golden CV 2 - Software Engineer"""
        cv_path = golden_cv_dir / "golden_cv_2_software_engineer.txt"
        
        if not cv_path.exists():
            pytest.skip(f"Golden CV not found: {cv_path}")
        
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        result = parser.parse(cv_text)
        
        # Assertions
        assert result.name is not None
        assert result.contact.email is not None
        assert len(result.skills) > 0
        assert len(result.experience) > 0
        assert len(result.education) > 0, "Software engineers typically have education listed"
        
        # Tech-specific expectations
        tech_skills = [s.normalized_skill.lower() for s in result.skills]
        assert any('python' in skill or 'java' in skill or 'javascript' in skill 
                  for skill in tech_skills), "Should detect programming languages"
    
    def test_golden_cv_3_data_scientist(self, parser, golden_cv_dir):
        """Test parsing of golden CV 3 - Data Scientist"""
        cv_path = golden_cv_dir / "golden_cv_3_data_scientist.txt"
        
        if not cv_path.exists():
            pytest.skip(f"Golden CV not found: {cv_path}")
        
        with open(cv_path, 'r', encoding='utf-8') as f:
            cv_text = f.read()
        
        result = parser.parse(cv_text)
        
        # Assertions
        assert result.name is not None
        assert result.contact.email is not None
        assert len(result.skills) > 5, "Data scientists typically have many technical skills"
        assert len(result.education) > 0, "Data scientists typically have advanced degrees"
        
        # Data science-specific expectations
        ds_skills = [s.normalized_skill.lower() for s in result.skills]
        assert any('python' in skill or 'machine learning' in skill or 'data' in skill 
                  for skill in ds_skills), "Should detect data science skills"
    
    def test_all_golden_cvs_have_minimum_quality(self, parser, golden_cv_dir):
        """Test that all golden CVs meet minimum parsing quality standards"""
        if not golden_cv_dir.exists():
            pytest.skip(f"Golden CV directory not found: {golden_cv_dir}")
        
        golden_cvs = list(golden_cv_dir.glob("golden_cv_*.txt"))
        
        if not golden_cvs:
            pytest.skip("No golden CVs found")
        
        for cv_path in golden_cvs:
            with open(cv_path, 'r', encoding='utf-8') as f:
                cv_text = f.read()
            
            result = parser.parse(cv_text)
            
            # Minimum quality standards
            assert result.extraction_confidence > 0.3, \
                f"{cv_path.name}: Extraction confidence too low ({result.extraction_confidence})"
            
            assert result.name is not None or result.contact.email is not None, \
                f"{cv_path.name}: Should extract at least name or email"
            
            assert len(result.skills) > 0 or len(result.experience) > 0, \
                f"{cv_path.name}: Should extract either skills or experience"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
