from backend.app.core.document_parser import DocumentParser
import json

def test_compliance_display():
    # Initialize document parser
    parser = DocumentParser()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLIANCE DISPLAY FUNCTION")
    print("=" * 80)
    
    # Sample compliance data
    compliance_data = {
        "overall_status": "Mostly Compliant",
        "areas": [
            {
                "name": "Data Protection",
                "status": "Partially Compliant",
                "relevance": "High",
                "risk_level": "Medium",
                "requirements_met": [
                    "Confidentiality Clause",
                    "Data Security Measures"
                ],
                "requirements_missing": [
                    "Data Breach Notification",
                    "Data Subject Rights"
                ]
            },
            {
                "name": "Contract Completeness",
                "status": "Non-Compliant",
                "relevance": "High",
                "risk_level": "High",
                "requirements_met": [
                    "Party Identification",
                    "Effective Date"
                ],
                "requirements_missing": [
                    "Governing Law",
                    "Dispute Resolution",
                    "Severability Clause"
                ]
            }
        ],
        "warnings": [
            {
                "message": "Missing key legal provisions that may affect enforceability",
                "level": "High"
            },
            {
                "message": "Data protection clauses inadequate for GDPR compliance",
                "level": "Medium"
            }
        ],
        "compliant_areas": [
            "Intellectual Property",
            "Termination Provisions"
        ],
        "recommendations": [
            "Add a governing law clause to specify applicable jurisdiction",
            "Include data breach notification requirements",
            "Add dispute resolution mechanisms"
        ],
        "visualization": {
            "areas": [
                {
                    "name": "Data Protection",
                    "status": "Partially Compliant",
                    "relevance": "High",
                    "relevance_score": 0.85,
                    "risk_level": "Medium",
                    "color": "#FFA500",
                    "requirements": {
                        "total": 4,
                        "met": 2,
                        "missing": 2
                    }
                },
                {
                    "name": "Contract Completeness",
                    "status": "Non-Compliant",
                    "relevance": "High",
                    "relevance_score": 0.95,
                    "risk_level": "High",
                    "color": "#FF0000",
                    "requirements": {
                        "total": 5,
                        "met": 2,
                        "missing": 3
                    }
                },
                {
                    "name": "Intellectual Property",
                    "status": "Compliant",
                    "relevance": "Medium",
                    "relevance_score": 0.65,
                    "risk_level": "Low",
                    "color": "#00FF00",
                    "requirements": {
                        "total": 3,
                        "met": 3,
                        "missing": 0
                    }
                }
            ],
            "compliance_score": 68.5
        },
        "detailed_results": {
            "Data Protection": {
                "status": "Partially Compliant",
                "requirements_contexts": {
                    "Confidentiality Clause": [
                        "Recipient shall not disclose any Confidential Information to third parties and shall use the same degree of care"
                    ],
                    "Data Breach Notification": []
                }
            },
            "Contract Completeness": {
                "status": "Non-Compliant",
                "requirements_contexts": {
                    "Party Identification": [
                        "This Confidentiality Agreement is entered into by and between ABC Corporation and XYZ LLC"
                    ],
                    "Governing Law": []
                }
            }
        }
    }
    
    print("\n" + "=" * 80)
    print("TEXT FORMAT OUTPUT")
    print("=" * 80)
    # Test text output format
    text_output = parser.display_compliance_check(compliance_data, 'text')
    print(text_output)
    
    print("\n" + "=" * 80)
    print("HTML FORMAT STRUCTURE (PREVIEW)")
    print("=" * 80)
    # Test HTML structure output
    html_output = parser.display_compliance_check(compliance_data, 'html')
    print(json.dumps(html_output, indent=2)[:500] + "..." if len(json.dumps(html_output, indent=2)) > 500 else json.dumps(html_output, indent=2))
    
    print("\n" + "=" * 80)
    print("JSON FORMAT OUTPUT (PREVIEW)")
    print("=" * 80)
    # Test JSON output format
    json_output = parser.display_compliance_check(compliance_data, 'json')
    print(json.dumps(json_output, indent=2)[:500] + "..." if len(json.dumps(json_output, indent=2)) > 500 else json.dumps(json_output, indent=2))

if __name__ == "__main__":
    test_compliance_display()
