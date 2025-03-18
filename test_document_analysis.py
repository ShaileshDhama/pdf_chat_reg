from backend.app.core.document_parser import DocumentParser
import json

def test_document_analysis():
    # Initialize document parser
    parser = DocumentParser()
    print("\n" + "=" * 80)
    print("TESTING DOCUMENT ANALYSIS FEATURES")
    print("=" * 80)
    
    # Sample legal text for testing (a small contract excerpt)
    sample_text = """
    CONFIDENTIALITY AGREEMENT
    
    This Confidentiality Agreement (the "Agreement") is entered into as of January 15, 2023 (the "Effective Date") by and between ABC Corporation, a Delaware corporation with its principal place of business at 123 Main Street, Anytown, USA ("Company"), and XYZ LLC, a California limited liability company with its principal place of business at 456 Oak Avenue, Othertown, USA ("Recipient").
    
    WHEREAS, Company and Recipient desire to exchange certain confidential information for the purpose of evaluating a potential business relationship (the "Purpose");
    
    NOW, THEREFORE, in consideration of the mutual covenants contained herein, the parties agree as follows:
    
    1. CONFIDENTIAL INFORMATION. "Confidential Information" means any information disclosed by Company to Recipient, either directly or indirectly, in writing, orally or by inspection of tangible objects, which is designated as "Confidential" or would reasonably be understood to be confidential given the nature of the information and circumstances of disclosure. Confidential Information includes, without limitation, technical data, trade secrets, know-how, research, product plans, products, services, customer lists, markets, software, developments, inventions, processes, formulas, technology, designs, drawings, engineering, hardware configuration information, marketing, finances or other business information.
    
    2. OBLIGATIONS. Recipient shall not disclose any Confidential Information to third parties and shall use the same degree of care, but no less than a reasonable degree of care, to protect the confidentiality of Confidential Information as it uses to protect its own confidential information of a similar nature. Recipient shall limit access to Confidential Information to those of its employees who need to know such information and who have signed confidentiality agreements with similar terms.
    
    3. TERM AND TERMINATION. The obligations of Recipient under this Agreement shall survive any termination of any business relationship between the parties and shall be binding upon Recipient's heirs, successors and assigns. Upon termination of this Agreement or at Company's request, Recipient shall promptly return or destroy all Confidential Information.
    
    IN WITNESS WHEREOF, the parties have executed this Agreement as of the Effective Date.
    
    ABC Corporation
    By: _________________________
    Name: John Smith
    Title: CEO
    
    XYZ LLC
    By: _________________________
    Name: Jane Doe
    Title: Managing Partner
    """
    
    print("\n" + "=" * 80)
    print("TOPIC EXTRACTION")
    print("=" * 80)
    # Test topic extraction
    topics = parser._extract_topics(sample_text)
    print("\nTop Document Topics:")
    for topic in topics[:3]:  # Show only the top 3 topics
        print(f"\nTopic: {topic['topic']}")
        print(f"Score: {topic['score']}")
        print(f"Type: {topic['type']}")
        if 'context' in topic and topic['context']:
            print("Context:")
            if isinstance(topic['context'], list):
                for ctx in topic['context'][:1]:  # Show just 1 context example
                    print(f"  - {ctx[:100]}..." if len(ctx) > 100 else f"  - {ctx}")
            else:
                print(f"  - {topic['context'][:100]}..." if len(topic['context']) > 100 else f"  - {topic['context']}")
    
    print("\n" + "=" * 80)
    print("LEGAL TERMS EXTRACTION")
    print("=" * 80)
    # Test legal terms extraction
    legal_terms = parser._extract_legal_terms(sample_text)
    print("\nExtracted Legal Terms:")
    for term in legal_terms[:3]:  # Display just the first 3 for brevity
        print(f"\nTerm: {term['term']}")
        print(f"Category: {term['category']}")
        print(f"Frequency: {term['frequency']}")
        if 'context' in term and term['context']:
            print(f"Context: {term['context'][:100]}..." if len(term['context']) > 100 else f"Context: {term['context']}")
        
    print("\n" + "=" * 80)
    print("COMPLIANCE CHECK")
    print("=" * 80) 
    # Test compliance check
    compliance = parser._check_compliance(sample_text)
    print(f"\nOverall Status: {compliance['overall_status']}")
    
    if 'visualization' in compliance:
        print(f"\nCompliance Score: {compliance['visualization']['compliance_score']}%")
        
        if 'areas' in compliance['visualization'] and compliance['visualization']['areas']:
            print("\nVisualization Areas:")
            for area in compliance['visualization']['areas'][:2]:  # Show first 2 areas
                print(f"\n  Area: {area['name']}")
                print(f"  Status: {area['status']}")
                print(f"  Relevance: {area['relevance']} ({area['relevance_score']})")
                print(f"  Risk Level: {area['risk_level']}")
                print(f"  Color: {area['color']}")
                if 'requirements' in area:
                    print(f"  Requirements: {area['requirements']['met']}/{area['requirements']['total']} met")
    
    if 'areas' in compliance and compliance['areas']:
        print("\nAreas with Issues:")
        for area in compliance['areas'][:1]:  # Just show 1 for brevity
            print(f"\n  Area: {area['name']}")
            print(f"  Status: {area['status']}")
            print(f"  Relevance: {area['relevance']}")
            print(f"  Risk Level: {area['risk_level']}")
            
            if 'requirements_met' in area and area['requirements_met']:
                print("\n  Requirements Met:")
                for req in area['requirements_met'][:1]:  # Show just 1 for brevity
                    print(f"    - {req}")
                    
            if 'requirements_missing' in area and area['requirements_missing']:
                print("\n  Requirements Missing:")
                for req in area['requirements_missing'][:1]:  # Show just 1 for brevity
                    print(f"    - {req}")
    
    if 'detailed_results' in compliance:
        print("\nDetailed Results Sample:")
        # Show details for one area with context examples
        for area_name, area_data in list(compliance['detailed_results'].items())[:1]:  # Just first area
            print(f"\n  Area: {area_name}")
            print(f"  Status: {area_data['status']}")
            
            if 'requirements_contexts' in area_data and area_data['requirements_contexts']:
                # Display context for one requirement
                for req_name, contexts in list(area_data['requirements_contexts'].items())[:1]:
                    print(f"\n  Context for '{req_name}':")
                    for ctx in contexts[:1]:  # Just show the first context
                        print(f"    {ctx[:150]}..." if len(ctx) > 150 else f"    {ctx}")
    
    if 'warnings' in compliance and compliance['warnings']:
        print("\nWarnings:")
        for warning in compliance['warnings'][:2]:  # Show top 2 warnings
            print(f"\n  - {warning['message']}")
            if 'level' in warning:
                print(f"    Severity: {warning['level']}")
    
    if 'compliant_areas' in compliance and compliance['compliant_areas']:
        print("\nCompliant Areas:")
        for area in compliance['compliant_areas'][:2]:  # Show top 2 compliant areas
            print(f"\n  - {area['name']} (Relevance: {area['relevance']})")
    
    if 'recommendations' in compliance and compliance['recommendations']:
        print("\nRecommendations:")
        for recommendation in compliance['recommendations']:
            print(f"\n  - {recommendation}")
    
    print("\nVisualization Data:")
    if 'visualization' in compliance and compliance['visualization']:
        viz_data = compliance['visualization']
        print(f"  Overall Compliance Score: {viz_data.get('compliance_score', 0)}%")
        
        if 'areas' in viz_data and viz_data['areas']:
            print("\n  Compliance Areas:")
            for area in viz_data['areas'][:3]:  # Show top 3 areas
                status_icon = "✓" if area['status'] == "Compliant" else "✗"
                print(f"    {status_icon} {area['name']}: {area['status']} (Risk: {area['risk_level']})")
    
    print("\n" + "=" * 80)
    print("SENTIMENT ANALYSIS")
    print("=" * 80)
    # Test sentiment analysis
    sentiment = parser._analyze_sentiment(sample_text)
    print("\nSentiment Analysis Results:")
    if 'overall' in sentiment:
        print(f"\nOverall Score: {sentiment['overall']['score']}")
        print(f"Overall Label: {sentiment['overall']['label']}")
        if 'confidence' in sentiment['overall']:
            print(f"Confidence: {sentiment['overall']['confidence']}")
    
    if 'breakdown' in sentiment and sentiment['breakdown']:
        print("\nSection Breakdown:")
        for i, section in enumerate(sentiment['breakdown'][:1]):  # Show just 1 section
            print(f"\nSection {i+1}:")
            for key, value in section.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"  {key}: {value[:100]}...")
                else:
                    print(f"  {key}: {value}")
    
    if 'key_sections' in sentiment and sentiment['key_sections']:
        print("\nKey Sections:")
        for i, section in enumerate(sentiment['key_sections'][:1]):  # Show just 1
            print(f"\n  Key Section {i+1}:")
            for key, value in section.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"    {key}: {value[:100]}...")
                else:
                    print(f"    {key}: {value}")
    
    if 'summary' in sentiment:
        print(f"\nSummary: {sentiment['summary'][:200]}..." if len(sentiment['summary']) > 200 else f"\nSummary: {sentiment['summary']}")
    
    print("\n" + "=" * 80)
    print("READABILITY METRICS")
    print("=" * 80)
    # Test readability
    readability = parser._calculate_readability(sample_text)
    print("\nReadability Metrics:")
    print(f"Score: {readability['score']}")
    print(f"Level: {readability['level']}")
    print(f"Word Count: {readability['word_count']}")
    print(f"Sentence Count: {readability['sentence_count']}")
    print(f"Avg Sentence Length: {readability['avg_sentence_length']}")
    print(f"Avg Syllables Per Word: {readability['avg_syllables_per_word']}")
    print(f"Reading Time (mins): {readability['reading_time_minutes']}")

    # Test compliance visualization display
    print("\n" + "=" * 80)
    print("COMPLIANCE VISUALIZATION")
    print("=" * 80)
    print("\nText Format Output:")
    compliance_display = parser.display_compliance_check(compliance, 'text')
    print(compliance_display)

    print("\nHTML Format Structure (preview):")
    html_output = parser.display_compliance_check(compliance, 'html')
    # Print a preview of the HTML structure
    print(json.dumps(html_output, indent=2)[:500] + "..." if len(json.dumps(html_output, indent=2)) > 500 else json.dumps(html_output, indent=2))

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_document_analysis()
