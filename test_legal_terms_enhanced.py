import sys
import os
import json
from pprint import pprint

# Add the backend path to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

# Import the DocumentParser class
from backend.app.core.document_parser import DocumentParser

def test_legal_terms_extraction():
    """
    Test the enhanced legal terms extraction functionality.
    """
    print("\n" + "=" * 80)
    print("TESTING ENHANCED LEGAL TERMS EXTRACTION")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample legal text with various legal terms
    sample_text = """
    This Agreement ("Agreement") is entered into as of the Effective Date, by and between 
    ACME Corporation, a Delaware corporation ("Company"), and John Doe, an individual ("Contractor").
    
    1. Confidentiality. Contractor acknowledges that during the provision of Services, 
    Contractor will have access to Company's confidential and proprietary information, including 
    but not limited to intellectual property, trade secrets, business plans, customer data, and 
    technical specifications ("Confidential Information"). Contractor agrees to maintain the 
    confidentiality of all Confidential Information and shall not disclose such information to 
    any third party without prior written consent of Company.
    
    2. Data Protection. Contractor shall comply with all applicable data protection laws including 
    GDPR and CCPA. Personal information shall only be processed in accordance with Company's 
    privacy policy and data processing agreement. Contractor shall implement appropriate technical 
    and organizational measures to protect personal data against unauthorized access.
    
    3. Intellectual Property. All work product, inventions, and intellectual property developed by 
    Contractor as part of the Services shall be the sole and exclusive property of Company. Contractor 
    hereby assigns all rights, title, and interest in such intellectual property to Company.
    
    4. Term and Termination. This Agreement shall commence on the Effective Date and continue for 
    a period of one year, unless earlier terminated. Either party may terminate this Agreement upon 
    30 days' written notice. In the event of a material breach, the non-breaching party may terminate 
    immediately upon written notice to the breaching party.
    
    5. Governing Law. This Agreement shall be governed by and construed in accordance with the laws 
    of the State of California. Any dispute arising under this Agreement shall be resolved in the 
    state or federal courts located in San Francisco County, California.
    
    6. HIPAA Compliance. If Contractor has access to Protected Health Information as defined under 
    HIPAA, Contractor agrees to comply with all applicable HIPAA requirements and to execute a 
    Business Associate Agreement if requested by Company.
    
    7. Force Majeure. Neither party shall be liable for any failure to perform due to causes beyond 
    its reasonable control including, but not limited to, acts of God, war, terrorism, riots, embargoes, 
    acts of civil or military authorities, fire, floods, earthquakes, or other natural disasters.
    """
    
    # Extract legal terms
    legal_terms = parser._extract_legal_terms(sample_text)
    
    # Display results
    print(f"\nExtracted {len(legal_terms)} legal terms.")
    print("\nTop 10 Most Important Legal Terms:")
    
    for idx, term in enumerate(legal_terms[:10], 1):
        print(f"\n{idx}. {term['term'].upper()} (Category: {term['category']})")
        print(f"   Importance: {term['importance']}")
        print(f"   Frequency: {term['frequency']}")
        
        # Display primary context with better formatting
        if 'primary_context' in term and term['primary_context']:
            context = term['primary_context']
            # Highlight the term in context
            highlighted = context.replace(term['term'], f"**{term['term']}**")
            print(f"\n   Context: ...{highlighted}...")
        elif 'context' in term and term['context']:
            context = term['context'][0] if isinstance(term['context'], list) and term['context'] else term['context']
            # Highlight the term in context
            highlighted = context.replace(term['term'], f"**{term['term']}**")
            print(f"\n   Context: ...{highlighted}...")

    # Test document position recognition
    early_terms = [term for term in legal_terms if hasattr(term, 'position') and term['position'] == 'early']
    if early_terms:
        print(f"\nFound {len(early_terms)} terms in early document position")
    
    # Test context extraction
    print("\nTesting Context Extraction:")
    sample_sentence = "This contract includes provisions related to confidentiality and intellectual property rights."
    sample_start = sample_sentence.find("confidentiality")
    sample_end = sample_start + len("confidentiality")
    
    context = parser._extract_term_context(sample_sentence, sample_start, sample_end)
    print(f"Original: {sample_sentence}")
    print(f"Extracted Context: {context}")

def test_recommendations():
    """
    Test the recommendations generation functionality.
    """
    print("\n" + "=" * 80)
    print("TESTING COMPLIANCE RECOMMENDATIONS")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample areas with issues
    sample_areas = [
        {
            "name": "GDPR Compliance",
            "status": "Partially Compliant",
            "risk_level": "high",
            "requirements_missing": ["Data Subject Rights", "International Transfer Provisions"]
        },
        {
            "name": "Contract Completeness",
            "status": "Partially Compliant",
            "risk_level": "medium",
            "requirements_missing": ["Governing Law", "Dispute Resolution"]
        },
        {
            "name": "HIPAA Compliance",
            "status": "Non-Compliant",
            "risk_level": "high",
            "requirements_missing": ["Business Associate Agreement", "PHI Safeguards"]
        }
    ]
    
    # Generate recommendations
    recommendations = parser._generate_compliance_recommendations(sample_areas)
    
    # Display results
    print(f"\nGenerated {len(recommendations)} recommendations:")
    for idx, rec in enumerate(recommendations, 1):
        print(f"\n{idx}. {rec}")

def test_enhanced_display():
    """
    Test the enhanced display capabilities for compliance results.
    """
    print("\n" + "=" * 80)
    print("TESTING ENHANCED DISPLAY")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample compliance data
    sample_compliance = {
        "overall_status": "Partially Compliant",
        "areas": [
            {
                "name": "GDPR Compliance",
                "status": "Partially Compliant",
                "relevance": "High",
                "risk_level": "high",
                "requirements_met": ["Privacy Policy", "Data Processing Records"],
                "requirements_missing": ["Data Subject Rights", "International Transfer Provisions"]
            },
            {
                "name": "HIPAA Compliance",
                "status": "Non-Compliant",
                "relevance": "Medium",
                "risk_level": "high",
                "requirements_met": [],
                "requirements_missing": ["Business Associate Agreement", "PHI Safeguards", "Minimum Necessary"]
            }
        ],
        "warnings": [
            {"message": "Missing critical HIPAA provisions", "level": "high"},
            {"message": "GDPR data subject rights not explicitly addressed", "level": "medium"}
        ],
        "compliant_areas": [
            {"name": "Contract Basics", "relevance": "High"},
            {"name": "Intellectual Property", "relevance": "Medium"}
        ],
        "visualization": {
            "areas": [
                {"name": "GDPR Compliance", "status": "Partially Compliant", "risk_level": "high", "color": "#FBBC05"},
                {"name": "HIPAA Compliance", "status": "Non-Compliant", "risk_level": "high", "color": "#EA4335"},
                {"name": "Contract Basics", "status": "Compliant", "risk_level": "low", "color": "#34A853"},
                {"name": "Intellectual Property", "status": "Compliant", "risk_level": "medium", "color": "#34A853"}
            ],
            "compliance_score": 62.5
        },
        "recommendations": [
            "Include explicit provisions for data subject rights (access, rectification, erasure, etc.)",
            "Include a Business Associate Agreement (BAA) for HIPAA compliance",
            "Specify safeguards for Protected Health Information (PHI)",
            "Include safeguards for international data transfers",
            "Consider legal consultation for comprehensive compliance"
        ]
    }
    
    # Display in different formats
    print("\nText Format:")
    text_output = parser.display_compliance_check(sample_compliance, 'text')
    print(text_output)
    
    print("\nHTML Format (Structure):")
    html_output = parser.display_compliance_check(sample_compliance, 'html')
    print(json.dumps(html_output, indent=2)[:500] + "..." if len(json.dumps(html_output, indent=2)) > 500 else json.dumps(html_output, indent=2))
    
    print("\nJSON Format (Partial):")
    json_output = parser.display_compliance_check(sample_compliance, 'json')
    print(json.dumps(json_output, indent=2)[:500] + "..." if len(json.dumps(json_output, indent=2)) > 500 else json.dumps(json_output, indent=2))

if __name__ == "__main__":
    test_legal_terms_extraction()
    test_recommendations()
    test_enhanced_display()
