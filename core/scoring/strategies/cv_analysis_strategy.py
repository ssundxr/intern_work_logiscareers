"""
CV Analysis Scoring Strategy

Extracted from ComprehensiveScorer._assess_cv()
Analyzes CV/Resume content for relevance and quality.

This strategy is responsible ONLY for CV analysis assessment.

Configuration: All scoring constants loaded from config.scoring_config.
"""

import re
from typing import List, Dict, Any
from config.scoring_config import scoring_config
from core.scoring.strategies.base import ScoringStrategy, ScoringContext
from core.scoring.models import CVAssessment


class CVAnalysisScoringStrategy(ScoringStrategy):
    """
    Strategy for analyzing CV/Resume content for relevance and quality.
    
    Evaluates:
    - CV quality score
    - Keyword match
    - Content relevance
    - Experience extraction
    - Skills extraction
    """
    
    def score(self, context: ScoringContext) -> CVAssessment:
        """
        Analyze CV/Resume content for relevance and quality.
        
        This is the EXACT logic from ComprehensiveScorer._assess_cv()
        with NO modifications to preserve bit-for-bit identical scoring.
        """
        cv_text = context.cv_text
        job_data = context.job_data
        candidate_data = context.candidate_data
        
        if not cv_text or len(cv_text.strip()) < 100:
            return CVAssessment(
                cv_score=50,
                cv_quality_score=50,
                content_relevance_score=50,
                keyword_match_score=50,
                experience_extraction_score=50,
                skills_extraction_score=50,
                explanation="CV text is too short or not available for detailed analysis",
                matched_keywords=[],
                missing_keywords=[],
                cv_insights={'warning': 'Insufficient CV content'}
            )
        
        cv_lower = cv_text.lower()
        cv_word_count = len(cv_text.split())
        
        # 1. CV Quality Score
        quality_indicators = {
            'contact_info': bool(re.search(r'[\w\.-]+@[\w\.-]+', cv_text)),  # email
            'phone': bool(re.search(r'[\+]?[\d\s\-\(\)]{10,}', cv_text)),
            'linkedin': 'linkedin' in cv_lower,
            'structured_sections': any(section in cv_lower for section in ['experience', 'education', 'skills', 'summary']),
            'adequate_length': cv_word_count >= 200,
            'achievements': any(word in cv_lower for word in ['achieved', 'increased', 'reduced', 'improved', 'managed', 'led'])
        }
        
        quality_score = int((sum(quality_indicators.values()) / len(quality_indicators)) * 100)
        
        # 2. Keyword Match Score
        # Only use explicit skills from required_skills and preferred_skills
        job_keywords = []
        for field in ['required_skills', 'preferred_skills', 'keywords']:
            skills = job_data.get(field, [])
            if isinstance(skills, list):
                job_keywords.extend(skills)
        
        # Extended stopwords list - filter out common English words
        stopwords = {
            'the', 'and', 'for', 'with', 'this', 'that', 'will', 'have', 'from', 'they', 
            'are', 'been', 'has', 'was', 'were', 'can', 'could', 'should', 'would', 'may',
            'our', 'your', 'their', 'his', 'her', 'its', 'who', 'what', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'some', 'any', 'many', 'much', 'more',
            'most', 'other', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'under', 'again', 'further', 'then', 'once', 'here',
            'there', 'when', 'where', 'why', 'how', 'all', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'only', 'own', 'same', 'than', 'too', 'very',
            'about', 'also', 'being', 'but', 'not', 'you', 'she', 'one', 'two', 'three',
            'applications', 'contribute', 'development', 'team', 'engineer', 'detail',
            'strong', 'career', 'level', 'motivated', 'scalable', 'fast', 'maintenance',
            'professionals', 'within', 'work', 'working', 'experience', 'position', 'role',
            'company', 'opportunity', 'looking', 'candidate', 'ideal', 'seeking', 'join',
            'dynamic', 'growing', 'dedicated', 'passionate', 'committed', 'focused',
            'responsible', 'required', 'preferred', 'must', 'able', 'ability', 'excellent',
            'good', 'great', 'best', 'top', 'high', 'well', 'years', 'year', 'degree',
            'duties', 'responsibilities', 'skills', 'requirements', 'qualifications'
        }
        
        # Clean and filter job keywords - only keep actual technical skills/tools
        job_keywords = list(set(k.lower().strip() for k in job_keywords if k and len(k.strip()) > 2 and k.lower().strip() not in stopwords))
        
        # Match keywords in CV
        matched_keywords = [kw for kw in job_keywords if kw in cv_lower]
        missing_keywords = [kw for kw in job_keywords if kw not in cv_lower][:10]  # Top 10 missing
        
        keyword_score = int((len(matched_keywords) / max(len(job_keywords), 1)) * 100) if job_keywords else 75
        
        # 3. Content Relevance Score
        industry = job_data.get('industry', '').lower()
        func_area = job_data.get('functional_area', '').lower()
        
        relevance_hits = sum([
            industry in cv_lower if industry else 0,
            func_area in cv_lower if func_area else 0,
            any(term in cv_lower for term in ['logistics', 'supply chain', 'warehouse', 'freight', 'shipping']),
            any(term in cv_lower for term in ['experience', 'years', 'worked', 'employed']),
        ])
        
        relevance_score = min(100, 50 + relevance_hits * 15)
        
        # 4. Experience Extraction Score
        experience_patterns = [
            re.search(r'\d+\+?\s*years?\s*(of\s*)?experience', cv_lower),
            re.search(r'experience\s*:\s*\d+', cv_lower),
            re.search(r'20\d{2}\s*[-–to]+\s*(20\d{2}|present|current)', cv_lower, re.I)
        ]
        
        exp_score = min(100, 50 + sum(1 for p in experience_patterns if p) * 20)
        
        # 5. Skills Extraction Score
        skills_section = bool(re.search(r'skills?\s*[:\-]', cv_lower))
        skill_bullets = len(re.findall(r'•|▪|◦|\*|-\s+[A-Z]', cv_text))
        
        skills_score = min(100, 50 + (25 if skills_section else 0) + min(skill_bullets * 5, 25))
        
        # Overall CV Score (weighted average)
        cv_score = int(
            quality_score * 0.15 +
            keyword_score * 0.30 +
            relevance_score * 0.25 +
            exp_score * 0.15 +
            skills_score * 0.15
        )
        
        # Generate explanation
        explanation_parts = []
        if cv_score >= 80:
            explanation_parts.append("CV shows strong alignment with job requirements")
        elif cv_score >= 60:
            explanation_parts.append("CV has moderate alignment with job requirements")
        else:
            explanation_parts.append("CV shows limited alignment with job requirements")
        
        if matched_keywords:
            explanation_parts.append(f"Found {len(matched_keywords)} matching keywords")
        if missing_keywords:
            explanation_parts.append(f"Missing key terms: {', '.join(missing_keywords[:5])}")
        
        return CVAssessment(
            cv_score=cv_score,
            cv_quality_score=quality_score,
            content_relevance_score=relevance_score,
            keyword_match_score=keyword_score,
            experience_extraction_score=exp_score,
            skills_extraction_score=skills_score,
            explanation='. '.join(explanation_parts),
            matched_keywords=matched_keywords[:20],
            missing_keywords=missing_keywords[:10],
            cv_insights={
                'word_count': cv_word_count,
                'has_email': quality_indicators['contact_info'],
                'has_phone': quality_indicators['phone'],
                'has_linkedin': quality_indicators['linkedin'],
                'has_structured_sections': quality_indicators['structured_sections'],
                'has_achievements': quality_indicators['achievements']
            }
        )
