import sys
import os
import json
from pprint import pprint

# Add the backend path to the system path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

# Import the DocumentParser class
from backend.app.core.document_parser import DocumentParser

def test_document_type_detection():
    """
    Test the document type detection functionality.
    """
    print("\n" + "=" * 80)
    print("TESTING DOCUMENT TYPE DETECTION")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample legal text - NDA
    nda_text = """
    MUTUAL NON-DISCLOSURE AGREEMENT
    
    This Mutual Non-Disclosure Agreement (the "Agreement") is entered into as of May 1, 2025, by and between:
    
    COMPANY A, a corporation organized and existing under the laws of Delaware, with its principal place of business 
    at 123 Main Street, Anytown, USA ("Company A"); and
    
    COMPANY B, a corporation organized and existing under the laws of California, with its principal place of business 
    at 456 Oak Avenue, Othertown, USA ("Company B").
    
    WHEREAS, Company A and Company B (each a "Party" and collectively, the "Parties") wish to explore a potential 
    business relationship (the "Purpose") and in connection with the Purpose, each Party may disclose to the other 
    certain confidential and proprietary information;
    
    NOW, THEREFORE, in consideration of the mutual covenants contained herein, the Parties agree as follows:
    
    1. Confidential Information. "Confidential Information" means any information disclosed by one Party (the "Disclosing Party") 
    to the other Party (the "Receiving Party"), either directly or indirectly, in writing, orally or by inspection of tangible 
    objects, which is designated as "Confidential," "Proprietary" or some similar designation, or that reasonably should be 
    understood to be confidential given the nature of the information and the circumstances of disclosure.
    
    2. Non-Disclosure and Non-Use. The Receiving Party shall maintain the Confidential Information in strict confidence and shall 
    not disclose any Confidential Information to any third party. The Receiving Party shall not use any Confidential Information 
    for any purpose except to evaluate and engage in discussions concerning the Purpose.
    
    3. Term and Termination. This Agreement shall remain in effect for a period of 3 years from the Effective Date, unless 
    terminated earlier by mutual written consent of the Parties.
    """
    
    # Sample policy text
    privacy_policy_text = """
    PRIVACY POLICY
    
    Last Updated: March 15, 2025
    
    This Privacy Policy describes how we collect, use, and share your personal information when you visit or make a purchase from our website.
    
    1. PERSONAL INFORMATION WE COLLECT
    
    When you visit the site, we automatically collect certain information about your device, including information about your web browser, 
    IP address, time zone, and some of the cookies that are installed on your device. Additionally, as you browse the site, we collect 
    information about the individual web pages or products that you view, what websites or search terms referred you to the site, and 
    information about how you interact with the site.
    
    2. HOW WE USE YOUR PERSONAL INFORMATION
    
    We use the personal information we collect to help us screen for potential risk and fraud, and more generally to improve and optimize 
    our site (for example, by generating analytics about how our customers browse and interact with the site, and to assess the success of 
    our marketing and advertising campaigns).
    
    3. SHARING YOUR PERSONAL INFORMATION
    
    We share your Personal Information with service providers to help us provide our services and fulfill our contracts with you. 
    We may share your Personal Information to comply with applicable laws and regulations, to respond to a subpoena, search warrant 
    or other lawful request for information we receive, or to otherwise protect our rights.
    
    4. GDPR COMPLIANCE
    
    If you are a resident of the European Economic Area, you have the right to access the Personal Information we hold about you, 
    to port it to a new service, and to ask that your Personal Information be corrected, updated, or erased.
    """
    
    # Sample corporate document
    board_resolution_text = """
    BOARD RESOLUTION
    
    ACME CORPORATION
    A Delaware Corporation
    
    RESOLUTIONS OF THE BOARD OF DIRECTORS
    
    The undersigned, being all the directors of ACME Corporation, a Delaware corporation (the "Corporation"), hereby adopt the 
    following resolutions:
    
    RESOLVED, that the Corporation is authorized to enter into a Series A Preferred Stock Purchase Agreement substantially in the 
    form presented to the Board of Directors.
    
    FURTHER RESOLVED, that the officers of the Corporation are authorized and directed to execute all documents and take all actions 
    necessary to effectuate the foregoing resolution.
    
    FURTHER RESOLVED, that the Secretary of the Corporation is authorized and directed to make the proper entries in the minute books 
    of the Corporation reflecting these resolutions.
    
    IN WITNESS WHEREOF, the undersigned have executed this resolution as of May 1, 2025.
    
    ___________________________
    John Smith, Director
    
    ___________________________
    Jane Doe, Director
    """
    
    # Test document type detection
    doc_types = [
        {"name": "NDA", "text": nda_text},
        {"name": "Privacy Policy", "text": privacy_policy_text},
        {"name": "Board Resolution", "text": board_resolution_text}
    ]
    
    for doc in doc_types:
        print(f"\nAnalyzing {doc['name']}...")
        result = parser._detect_document_type(doc["text"])
        print(f"Detected document type: {result['document_type']}")
        if result['sub_type']:
            print(f"Sub-type: {result['sub_type']}")
        print(f"Confidence: {result['confidence']:.2f}")
        if result['indicators']:
            print(f"Key indicators: {', '.join(result['indicators'][:5])}")

def test_key_clause_extraction():
    """
    Test the key clause extraction functionality.
    """
    print("\n" + "=" * 80)
    print("TESTING KEY CLAUSE EXTRACTION")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample contract with various clauses
    contract_text = """
    SERVICE AGREEMENT
    
    This Service Agreement ("Agreement") is entered into as of June 1, 2025, by and between Client and Service Provider.
    
    1. Scope of Services. Service Provider shall provide the services described in Exhibit A (the "Services").
    
    2. Payment Terms. Client shall pay Service Provider the fees set forth in Exhibit B. Payments are due within 30 days of receipt of an invoice.
    
    3. Term and Termination. This Agreement shall commence on the Effective Date and continue for a period of one (1) year, unless earlier terminated. Either party may terminate this Agreement upon thirty (30) days' prior written notice to the other party. In the event of a material breach, the non-breaching party may terminate this Agreement immediately upon written notice.
    
    4. Confidentiality. Each party shall maintain the confidentiality of all confidential information disclosed by the other party. Confidential information shall include, but not be limited to, business plans, financial information, customer lists, and technical data. Each party shall use the same degree of care to protect the other party's confidential information as it uses to protect its own confidential information, but in no event less than reasonable care.
    
    5. Intellectual Property. All intellectual property developed by Service Provider in the course of providing the Services shall be owned by Client. Service Provider hereby assigns all rights, title, and interest in such intellectual property to Client.
    
    6. Limitation of Liability. IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING OUT OF OR RELATED TO THIS AGREEMENT, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES. EACH PARTY'S TOTAL LIABILITY SHALL NOT EXCEED THE FEES PAID BY CLIENT TO SERVICE PROVIDER DURING THE SIX (6) MONTHS PRECEDING THE CLAIM.
    
    7. Data Protection. Each party shall comply with all applicable data protection laws. Service Provider shall implement appropriate technical and organizational measures to protect personal data processed on behalf of Client.
    
    8. Governing Law. This Agreement shall be governed by and construed in accordance with the laws of the State of New York, without giving effect to any choice of law or conflict of law provisions. Any disputes shall be resolved in the courts of New York County, New York.
    
    9. Force Majeure. Neither party shall be liable for any failure or delay in performance due to causes beyond its reasonable control, including but not limited to acts of God, natural disasters, pandemics, government restrictions, or other similar events.
    
    10. Entire Agreement. This Agreement constitutes the entire understanding between the parties concerning the subject matter hereof and supersedes all prior agreements, understandings, or negotiations.
    """
    
    # Extract key clauses
    clauses = parser._extract_key_clauses(contract_text)
    
    # Display results
    print(f"\nExtracted {len(clauses)} key clauses.")
    print("\nKey Clauses by Importance:")
    
    for idx, clause in enumerate(clauses, 1):
        print(f"\n{idx}. {clause['clause_type']}")
        print(f"   Importance: {clause['importance']}")
        print(f"   Risk Score: {clause['risk_score']}")
        print(f"   Content: {clause['content'][:150]}{'...' if len(clause['content']) > 150 else ''}")

def test_integrated_compliance_check():
    """
    Test the integrated compliance check with document type and key clauses.
    """
    print("\n" + "=" * 80)
    print("TESTING INTEGRATED COMPLIANCE CHECK")
    print("=" * 80)
    
    parser = DocumentParser()
    
    # Sample GDPR-related document
    gdpr_doc = """
    DATA PROCESSING AGREEMENT
    
    This Data Processing Agreement ("DPA") is entered into between the Controller and the Processor.
    
    1. Definitions.
       1.1 "Controller" means the entity that determines the purposes and means of the Processing of Personal Data.
       1.2 "Processor" means the entity that Processes Personal Data on behalf of the Controller.
       1.3 "GDPR" means the General Data Protection Regulation (EU) 2016/679.
       1.4 "Personal Data" means any information relating to an identified or identifiable natural person.
       1.5 "Processing" means any operation performed on Personal Data.
    
    2. Data Processing.
       2.1 The Processor shall Process Personal Data only on documented instructions from the Controller.
       2.2 The Processor shall ensure that persons authorized to Process the Personal Data have committed themselves to confidentiality.
       2.3 The Processor shall implement appropriate technical and organizational measures to ensure a level of security appropriate to the risk.
    
    3. Sub-processors.
       3.1 The Processor shall not engage another processor without prior specific or general written authorization of the Controller.
       3.2 Where the Processor engages another processor, the same data protection obligations shall be imposed on that other processor.
    
    4. Data Subject Rights.
       4.1 The Processor shall assist the Controller in responding to requests for exercising the data subject's rights under the GDPR.
    
    5. Personal Data Breach.
       5.1 The Processor shall notify the Controller without undue delay after becoming aware of a Personal Data Breach.
    
    6. Data Protection Impact Assessment.
       6.1 The Processor shall provide assistance to the Controller in ensuring compliance with the obligations pursuant to Articles 32 to 36 of the GDPR.
    
    7. Return or Deletion of Data.
       7.1 At the choice of the Controller, the Processor shall delete or return all the Personal Data to the Controller after the end of the provision of services.
    
    8. Demonstration of Compliance.
       8.1 The Processor shall make available to the Controller all information necessary to demonstrate compliance with the obligations laid down in Article 28 of the GDPR.
    
    9. International Transfers.
       9.1 The Processor shall not transfer Personal Data to a third country or an international organization without the Controller's prior written authorization.
    """
    
    print("\nCalling compliance check...")
    # Run compliance check
    try:
        compliance_result = parser._check_compliance(gdpr_doc)
        print(f"Compliance result type: {type(compliance_result)}")
        print(f"Compliance result keys: {list(compliance_result.keys()) if isinstance(compliance_result, dict) else 'Not a dict'}")
    except Exception as e:
        print(f"Error in compliance check: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Display document type and key clauses from compliance result
    print("\nDocument Type Information:")
    if 'document_type' in compliance_result:
        doc_type = compliance_result['document_type']
        print(f"  Type: {doc_type.get('document_type', 'Unknown')}")
        if doc_type.get('sub_type'):
            print(f"  Sub-type: {doc_type['sub_type']}")
        print(f"  Confidence: {doc_type.get('confidence', 0):.2f}")
        if doc_type.get('indicators'):
            print(f"  Indicators: {', '.join(doc_type.get('indicators', [])[:5])}")
    else:
        print("  Document type information not available")
    
    print("\nKey Clauses:")
    if 'key_clauses' in compliance_result and compliance_result['key_clauses']:
        for idx, clause in enumerate(compliance_result['key_clauses'][:3], 1):  # Show top 3
            print(f"  {idx}. {clause['clause_type']} (Importance: {clause['importance']}, Risk: {clause['risk_score']})")
            # Print a snippet of the clause content
            content = clause['content'][:100] + "..." if len(clause['content']) > 100 else clause['content']
            print(f"     {content}")
    else:
        print("  Key clauses not available")
    
    # Display compliance areas
    print("\nCompliance Areas:")
    if 'areas' in compliance_result and isinstance(compliance_result['areas'], dict):
        for area_name, data in compliance_result['areas'].items():
            status = data.get('status', 'Unknown')
            status_icon = "" if status == "Compliant" else ""
            print(f"  {status_icon} {area_name}: {status}")
            
            # Show requirements if there are issues
            if status != "Compliant" and 'requirements_missing' in data and data['requirements_missing']:
                print("    Missing requirements:")
                for req in data['requirements_missing'][:2]:  # Show top 2 missing requirements
                    print(f"    - {req}")
    else:
        print("  No compliance areas available or format not as expected")
        # Print what we got to debug
        print(f"  Compliance result type: {type(compliance_result)}")
        if isinstance(compliance_result, dict):
            print(f"  Compliance result keys: {list(compliance_result.keys())}")

if __name__ == "__main__":
    test_document_type_detection()
    test_key_clause_extraction()
    test_integrated_compliance_check()
