"""
Test Script for POST /api/v1/compare Endpoint

This script demonstrates how to use the /compare endpoint with sample data.
It includes examples of HTML-formatted job descriptions and candidate profiles.

Usage:
    python test_compare_endpoint.py

Requirements:
    - Server running on http://localhost:8000
    - API_KEY environment variable set (if required)
"""

import json
import os
import requests
from typing import Dict, Any


# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")  # Set to empty string if not required


def create_sample_job() -> Dict[str, Any]:
    """Create a sample job posting with HTML-formatted description."""
    return {
        "job_id": "JOB-2025-001",
        "company_name": "Global Logistics Solutions",
        "company_type": "Employer",
        "country": "UAE",
        "state": "Dubai",
        "city": "Dubai",
        "title": "Senior Logistics Manager",
        "job_type": "Full-time",
        "industry": "Logistics & Supply Chain",
        "sub_industry": "Freight Forwarding",
        "functional_area": "Supply Chain Management",
        "designation": "Manager",
        "job_status": "Active",
        "min_experience_years": 7,
        "max_experience_years": 12,
        "require_gcc_experience": True,
        "salary_min": 18000,
        "salary_max": 25000,
        "currency": "AED",
        "hide_salary": False,
        "required_skills": [
            "Logistics Management",
            "Supply Chain Management",
            "3PL Operations",
            "Warehouse Management",
            "Inventory Control"
        ],
        "preferred_skills": [
            "SAP",
            "Six Sigma",
            "Lean Management",
            "WMS Software"
        ],
        "required_education": "Bachelors",
        "job_description": """
            <div class="job-description">
                <h2>About the Role</h2>
                <p>We are seeking an experienced <strong>Senior Logistics Manager</strong> to lead our supply chain operations in Dubai.</p>
                
                <h3>Key Responsibilities:</h3>
                <ul>
                    <li>Oversee <span class="highlight">end-to-end logistics operations</span></li>
                    <li>Manage warehouse and inventory control systems</li>
                    <li>Coordinate with international freight partners</li>
                    <li>Optimize supply chain processes for cost efficiency</li>
                    <li>Lead a team of 15+ logistics professionals</li>
                </ul>
                
                <h3>Requirements:</h3>
                <p>Minimum <strong>7 years</strong> of logistics experience, with at least <strong>5 years in GCC region</strong>. 
                Strong knowledge of 3PL operations and warehouse management systems required.</p>
            </div>
        """,
        "desired_candidate_profile": """
            <p>Ideal candidate is a <strong>proactive logistics professional</strong> with proven leadership skills 
            and deep understanding of supply chain optimization in the GCC market.</p>
        """
    }


def create_sample_candidate() -> Dict[str, Any]:
    """Create a sample candidate with HTML-formatted profile."""
    return {
        "candidate_id": "CAND-1001771",
        "registration_number": "CAN1001771",
        "full_name": "Ahmed Mohammed",
        "nationality": "Egyptian",
        "current_country": "UAE",
        "current_city": "Dubai",
        "visa_status": "Work Visa",
        "total_experience_years": 9.5,
        "gcc_experience_years": 8.0,
        "expected_salary": 22000,
        "currency": "AED",
        "skills": [
            "Logistics Management",
            "Supply Chain Management",
            "3PL Operations",
            "Warehouse Management",
            "Inventory Control",
            "SAP",
            "Six Sigma Certified",
            "Freight Forwarding",
            "Import/Export",
            "Team Leadership"
        ],
        "professional_skills": [
            "3PL Operations",
            "Air Freight",
            "Sea Freight",
            "Customs Clearance"
        ],
        "it_skills_certifications": [
            "SAP MM/SD",
            "Six Sigma Green Belt",
            "WMS - Manhattan"
        ],
        "education_level": "Bachelors",
        "employment_summary": """
            <div class="profile-summary">
                <p>Results-driven <strong>Logistics Manager</strong> with <strong>9+ years</strong> of comprehensive experience 
                in supply chain management and 3PL operations across the GCC region.</p>
                
                <p>Demonstrated expertise in:</p>
                <ul>
                    <li>Managing multi-million dollar logistics operations</li>
                    <li>Leading cross-functional teams of 20+ professionals</li>
                    <li>Implementing SAP-based warehouse management systems</li>
                    <li>Achieving <span class="metric">15% cost reduction</span> through process optimization</li>
                </ul>
            </div>
        """,
        "cv_text": """
            Ahmed Mohammed - Senior Logistics Professional
            
            PROFESSIONAL SUMMARY
            Accomplished logistics manager with 9+ years of experience in supply chain management, 
            warehouse operations, and 3PL services. Proven track record of optimizing logistics 
            processes, reducing costs, and leading high-performing teams in the UAE market.
            
            CORE COMPETENCIES
            • Supply Chain Management & Optimization
            • 3PL & Warehouse Operations
            • SAP MM/SD Implementation
            • Team Leadership & Development
            • Inventory Control & Management
            • Six Sigma Process Improvement
            • Freight Forwarding (Air & Sea)
            • Customs & Compliance
            
            PROFESSIONAL EXPERIENCE
            
            Senior Logistics Manager | Emirates Logistics LLC, Dubai | 2020 - Present
            - Manage end-to-end logistics operations for 200+ clients
            - Oversee warehouse network of 50,000 sq ft with inventory worth $5M
            - Lead team of 18 logistics coordinators and warehouse staff
            - Implemented SAP WMS resulting in 20% efficiency improvement
            - Reduced delivery time by 25% through route optimization
            
            Logistics Coordinator | Global Freight Solutions, Dubai | 2018 - 2020
            - Coordinated international shipments across 15+ countries
            - Managed customs clearance and documentation
            - Achieved 98% on-time delivery rate
            
            EDUCATION
            Bachelor of Commerce | Cairo University | 2013
            
            CERTIFICATIONS
            • Six Sigma Green Belt
            • SAP MM/SD Certified
            • IATA Dangerous Goods Handling
        """
    }


def compare_candidate_to_job(job: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the /api/v1/compare endpoint.
    
    Args:
        job: Job posting data
        candidate: Candidate profile data
    
    Returns:
        Evaluation response
    """
    url = f"{API_BASE_URL}/api/v1/compare"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add API key if configured
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    payload = {
        "job": job,
        "candidate": candidate
    }
    
    print(f"🔍 Calling {url}")
    print(f"📦 Payload size: {len(json.dumps(payload))} bytes")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        
        result = response.json()
        return result
    
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server")
        print(f"   Make sure the server is running at {API_BASE_URL}")
        return None
    
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {response.text}")
        return None
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def print_evaluation_summary(result: Dict[str, Any]):
    """Print a formatted summary of the evaluation result."""
    if not result:
        return
    
    print("=" * 80)
    print("📊 EVALUATION RESULTS")
    print("=" * 80)
    print()
    
    # Overall Score
    print(f"🎯 Overall Score: {result.get('overall_score', result.get('total_score'))}/100")
    print(f"📈 Decision: {result.get('decision')}")
    print()
    
    # Confidence
    if conf := result.get('confidence_metrics'):
        print(f"🔒 Confidence: {conf.get('confidence_level')} ({conf.get('confidence_score', 0):.2f})")
        print(f"   Data Completeness: {conf.get('data_completeness', 0):.2%}")
        print()
    
    # Section Scores
    if sections := result.get('section_scores'):
        print("📋 Section Breakdown:")
        for section_name, section_data in sections.items():
            score = section_data.get('score', 0)
            weight = section_data.get('weight', 0)
            contribution = section_data.get('contribution', 0)
            print(f"   • {section_name.capitalize()}: {score}/100 "
                  f"(weight: {weight:.1%}, contribution: {contribution:.1f})")
        print()
    
    # Strengths
    if strengths := result.get('strengths'):
        print("✅ Strengths:")
        for strength in strengths:
            print(f"   • {strength}")
        print()
    
    # Concerns
    if concerns := result.get('concerns'):
        print("⚠️  Concerns:")
        for concern in concerns:
            print(f"   • {concern}")
        print()
    
    # Skills Detail
    print("🛠️  Skills Analysis:")
    print(f"   Matched Required: {len(result.get('matched_required_skills', []))}")
    print(f"   Missing Required: {len(result.get('missing_required_skills', []))}")
    print(f"   Matched Preferred: {len(result.get('matched_preferred_skills', []))}")
    print()
    
    if missing_req := result.get('missing_required_skills'):
        print(f"   Missing: {', '.join(missing_req[:5])}")
        print()
    
    # Contextual Adjustments
    if adjustments := result.get('contextual_adjustments'):
        print("⚙️  Contextual Adjustments:")
        for adj in adjustments:
            sign = "+" if adj.get('impact', 0) > 0 else ""
            print(f"   • {adj.get('rule_name')}: {sign}{adj.get('impact')} points")
            print(f"     Reason: {adj.get('reason')}")
        print()
    
    # Performance
    if perf := result.get('performance_metrics'):
        print(f"⏱️  Performance: {perf.get('evaluation_time_ms', 0):.1f}ms")
        print(f"   Rules Evaluated: {perf.get('rules_evaluated', 0)}")
        print()
    
    print("=" * 80)


def main():
    """Main test function."""
    print("\n" + "=" * 80)
    print("🧪 Testing POST /api/v1/compare Endpoint")
    print("=" * 80)
    print()
    
    # Create test data
    print("📝 Creating test data...")
    job = create_sample_job()
    candidate = create_sample_candidate()
    print(f"   Job: {job['title']} at {job['company_name']}")
    print(f"   Candidate: {candidate['candidate_id']} ({candidate['total_experience_years']} years exp)")
    print()
    
    # Call API
    result = compare_candidate_to_job(job, candidate)
    
    # Print results
    if result:
        print_evaluation_summary(result)
        
        # Save full response to file
        output_file = "compare_endpoint_response.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"💾 Full response saved to: {output_file}")
    else:
        print("❌ Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
