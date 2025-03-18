import streamlit as st
import os
from pathlib import Path
import tempfile
from datetime import datetime
from backend.app.ai.document_analyzer import DocumentAnalyzer
from backend.app.core.document_service import DocumentService
import pandas as pd
import base64
from PIL import Image
import re

# Initialize services
document_service = DocumentService()

# Initialize session state for document storage
if 'documents' not in st.session_state:
    st.session_state.documents = []
if 'current_document' not in st.session_state:
    st.session_state.current_document = None

# Load LEGALe TROY logo from file
logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")

# Function to get image as base64 string (for CSS background images)
def get_img_as_base64(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Page config
st.set_page_config(
    page_title="LEGALe TROY",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with LEGALe TROY branding colors
st.markdown("""
<style>
    /* LEGALe TROY theme colors */
    :root {
        --bg-color: #F7F7F8;
        --secondary-bg: #FFFFFF;
        --text-color: #1A202C;
        --primary-color: #151C3B; /* Navy blue */
        --secondary-color: #D6B577; /* Gold */
        --accent-color: #2D3A80; /* Lighter blue */
        --error-color: #E53E3E;
        --success-color: #38A169;
        --warning-color: #ECC94B;
    }

    /* Main container */
    .main {
        background-color: var(--bg-color);
        color: var(--text-color);
        padding: 2rem;
    }
    
    /* Page heading */
    h1, h2, h3 {
        color: var(--primary-color);
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 600;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: var(--primary-color);
        color: white;
    }
    
    .sidebar .sidebar-content h1 {
        color: white;
    }
    
    /* Sidebar widgets */
    .sidebar .stRadio > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
    }
    
    .sidebar .stRadio label {
        color: white !important;
    }
    
    /* Upload area */
    .uploadArea {
        border: 2px dashed var(--secondary-color);
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #FFFFFF;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .uploadArea:hover {
        border-color: var(--primary-color);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Logo container */
    .logo-container {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .logo-image {
        width: 60px;
        margin-right: 15px;
    }
    
    .logo-text {
        display: inline-block;
        font-size: 24px;
        font-weight: 700;
        color: white;
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Brand tag */
    .brand-tag {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--secondary-color);
        font-weight: 600;
        margin-top: -5px;
    }
    
    /* Metrics card */
    .metric-card {
        background: var(--secondary-bg);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        border: none;
        transition: all 0.3s;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .stButton > button:hover {
        background-color: var(--accent-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Analysis results */
    .analysis-result {
        background: var(--secondary-bg);
        padding: 1.5rem;
        border-radius: 12px;
        margin-top: 1rem;
        border: 1px solid rgba(0, 0, 0, 0.05);
        animation: slideIn 0.3s ease-out;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--secondary-bg);
        padding: 0.5rem;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: var(--text-color);
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Risk indicators */
    .risk-high {
        color: #E53E3E;
        font-weight: bold;
    }
    
    .risk-medium {
        color: #DD6B20;
        font-weight: bold;
    }
    
    .risk-low {
        color: #38A169;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def get_img_as_base64(base64_string):
    return f"data:image/png;base64,{base64_string}"

# Initialize session state
if 'document_analyzer' not in st.session_state:
    st.session_state.document_analyzer = DocumentAnalyzer()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

def upload_document():
    """Handle document upload and analysis."""
    st.header("Document Upload & Analysis", divider="blue")
    
    # Upload Area
    st.markdown('<div class="uploadArea">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        label="Drop your document here or click to browse",
        type=["pdf", "doc", "docx", "txt"],
        key="doc_upload",
        label_visibility="visible"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_file:
        # Save file temporarily
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_path = tmp_file.name
        except Exception as e:
            st.error(f"Error saving file: {str(e)}")
            return
            
        try:
            # File info with enhanced metrics
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            cols = st.columns(4)
            
            # Basic file info
            try:
                cols[0].metric(
                    label="File Size",
                    value=f"{uploaded_file.size/1024:.1f} KB",
                    label_visibility="visible"
                )
                cols[1].metric(
                    label="File Type",
                    value=uploaded_file.type.split('/')[-1].upper(),
                    label_visibility="visible"
                )
            except Exception as e:
                st.error(f"Error displaying basic file metrics: {str(e)}")
            
            # Get document info
            try:
                doc_info = document_service.get_document_info(file_path)
                cols[2].metric(
                    label="Pages",
                    value=doc_info.get("page_count", "N/A"),
                    label_visibility="visible"
                )
                cols[3].metric(
                    label="Last Modified",
                    value=datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d"),
                    label_visibility="visible"
                )
            except Exception as e:
                st.error(f"Error displaying document info metrics: {str(e)}")
        except Exception as e:
            st.error(f"Error displaying file metrics: {str(e)}")
        finally:
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Analysis options
            with st.expander("Analysis Options", expanded=True):
                analysis_type = st.radio(
                    label="Select Analysis Type",
                    options=["Basic", "Detailed", "Legal"],
                    horizontal=True,
                    label_visibility="visible"
                )
                
                extract_entities = st.checkbox(
                    label="Extract Entities",
                    value=True,
                    help="Extract named entities like people, organizations, dates, etc.",
                    label_visibility="visible"
                )
                
                perform_ocr = st.checkbox(
                    label="Perform OCR",
                    value=True,
                    help="Extract text from images and scanned documents",
                    label_visibility="visible"
                )
            
            if st.button("Analyze Document", key="analyze_btn", use_container_width=True):
                with st.spinner("Analyzing document..."):
                    try:
                        # Process document with progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Step 1: Basic text extraction
                        status_text.text("Extracting text...")
                        progress_bar.progress(20)
                        
                        # Step 2: OCR if needed
                        if perform_ocr:
                            status_text.text("Performing OCR...")
                            progress_bar.progress(40)
                        
                        # Step 3: Entity extraction
                        if extract_entities:
                            status_text.text("Extracting entities...")
                            progress_bar.progress(60)
                        
                        # Step 4: Document analysis
                        status_text.text("Analyzing content...")
                        try:
                            analysis_result = document_service.analyze_document(
                                file_path,
                                analysis_type=analysis_type.lower(),
                                extract_entities=extract_entities,
                                perform_ocr=perform_ocr
                            )
                        except Exception as analysis_error:
                            st.error(f"Analysis error: {str(analysis_error)}")
                            st.warning("Continuing with partial results. Some metrics may show as zero.")
                            # Create a basic result structure to avoid further errors
                            analysis_result = {
                                "file_info": {
                                    "name": uploaded_file.name,
                                    "size": uploaded_file.size,
                                    "type": uploaded_file.type.split('/')[-1].upper()
                                },
                                "metadata": {},
                                "content": {"text": "", "summary": "Analysis failed. Please try again."},
                                "analysis": {
                                    "readability": 0,
                                    "sentiment": {"score": 0},
                                    "legal_terms": []
                                }
                            }
                        progress_bar.progress(80)
                        
                        # Step 5: Save results
                        status_text.text("Saving results...")
                        st.session_state.current_document = {
                            "path": file_path,
                            "name": uploaded_file.name,
                            "analysis": analysis_result
                        }
                        if st.session_state.current_document not in st.session_state.documents:
                            st.session_state.documents.append(st.session_state.current_document)
                        progress_bar.progress(100)
                        status_text.text("Analysis complete!")
                        
                        # Display results
                        display_document_analysis_results(analysis_result)
                        
                    except Exception as e:
                        st.error(f"Error analyzing document: {str(e)}")
                    finally:
                        # Cleanup
                        try:
                            os.unlink(file_path)
                        except:
                            pass

def view_documents():
    """Display analyzed documents and their results."""
    st.header("Document Library", divider="blue")
    
    if not st.session_state.documents:
        st.info("No documents analyzed yet. Upload a document to get started!")
        return
    
    # Document selection
    doc_names = [doc["name"] for doc in st.session_state.documents]
    selected_doc = st.selectbox(
        label="Select Document",
        options=doc_names,
        label_visibility="visible"
    )
    
    if selected_doc:
        doc = next(doc for doc in st.session_state.documents if doc["name"] == selected_doc)
        st.session_state.current_document = doc
        display_document_analysis_results(doc["analysis"])

def display_document_analysis_results(result):
    """Display complete document analysis results with improved visualization"""
    st.subheader("📊 Document Analysis Results")
    
    # Create tabs for different sections of analysis
    overview_tab, metrics_tab, content_tab, legal_tab = st.tabs(["Overview", "Metrics", "Content Analysis", "Legal Analysis"])
    
    with overview_tab:
        # Document overview in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📄 Document Information")
            st.markdown(f"**File Name:** {result['file_info']['name']}")
            st.markdown(f"**File Type:** {result['file_info']['type']}")
            st.markdown(f"**Size:** {format_file_size(result['file_info']['size'])}")
            st.markdown(f"**Pages:** {result['file_info'].get('page_count', 'N/A')}")
        
        with col2:
            st.markdown("### 🔍 Analysis Information")
            st.markdown(f"**Document Type:** {result['file_info'].get('document_type', 'Unknown').title()}")
            st.markdown(f"**Language:** {result['file_info'].get('language', 'en').upper()}")
            st.markdown(f"**Analysis Duration:** {result['file_info'].get('analysis_duration_ms', 0)} ms")
            st.markdown(f"**Analyzed At:** {result['file_info'].get('analyzed_at', '')}")
        
        # Summary section
        st.markdown("### 📝 Document Summary")
        st.markdown(result['content'].get('summary', 'No summary available'))
    
    with metrics_tab:
        st.markdown("### 📊 Document Metrics")
        
        # Use metric cards for key metrics
        metrics_columns = st.columns(4)
        
        # Word Count
        word_count = 0
        document_content = ""
        
        # Try different possible content paths in the result structure
        if 'content' in result:
            if isinstance(result['content'], str):
                document_content = result['content']
            elif isinstance(result['content'], dict) and 'text' in result['content']:
                document_content = result['content']['text']
        
        if document_content:
            words = re.findall(r'\b[^\W\d_]+\b', document_content)
            word_count = len(words)
        
        # Readability score
        readability_score = result['analysis'].get('readability_score', 0)
        readability_label = get_readability_label(readability_score)
        
        # Legal terms count
        legal_term_count = len(result['analysis'].get('legal_terms', []))
        
        # Sentiment score
        sentiment = result['analysis'].get('sentiment', {})
        sentiment_score = sentiment.get('score', 0)
        sentiment_label = sentiment.get('label', 'neutral').capitalize()
        
        # Display metrics in columns
        with metrics_columns[0]:
            st.metric("Word Count", word_count)
        
        with metrics_columns[1]:
            st.metric("Readability", f"{readability_score:.1f}")
            st.caption(readability_label)
        
        with metrics_columns[2]:
            st.metric("Legal Terms", legal_term_count)
        
        with metrics_columns[3]:
            st.metric("Sentiment", f"{sentiment_score:.2f}")
            st.caption(sentiment_label)
        
        # Display detailed metrics if available
        st.markdown("### 📏 Detailed Text Metrics")
        
        # Get document content from various possible locations in the structure
        document_content = ""
        if 'content' in result:
            if isinstance(result['content'], str):
                document_content = result['content']
            elif isinstance(result['content'], dict) and 'text' in result['content']:
                document_content = result['content']['text']
        
        col1, col2 = st.columns(2)
        with col1:
            # Count sentences and paragraphs
            sentences = re.split(r'[.!?]\s', document_content)
            paragraphs = re.split(r'\n\s*\n', document_content)
            
            sentence_count = len([s for s in sentences if s.strip()])
            paragraph_count = len([p for p in paragraphs if p.strip()])
            
            avg_sent_length = 0
            if sentence_count > 0 and word_count > 0:
                avg_sent_length = word_count / sentence_count
            
            st.metric("Sentences", sentence_count)
            st.metric("Average Words per Sentence", f"{avg_sent_length:.1f}")
        
        with col2:
            st.metric("Paragraphs", paragraph_count)
            
            # Estimate reading time (average reading speed: 250 words per minute)
            reading_time = word_count / 250
            st.metric("Reading Time", f"{reading_time:.1f} min")
    
    with content_tab:
        # Sentiment Analysis section
        st.markdown("### 🌡️ Sentiment Analysis")
        
        # Get sentiment information
        sentiment = result['analysis'].get('sentiment', {})
        sentiment_score = sentiment.get('score', 0)
        sentiment_label = sentiment.get('label', 'Neutral').capitalize()
        sentiment_confidence = sentiment.get('confidence', 0)
        
        # Display sentiment score and label
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"<h1 style='font-size: 2.5rem; margin: 0;'>{sentiment_score:.2f}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p>Label: {sentiment_label} (Confidence: {sentiment_confidence:.2f})</p>", unsafe_allow_html=True)
            
        with col2:
            # Calculate percentage for the progress bar (transform from -1...1 to 0...100)
            sentiment_percentage = (sentiment_score + 1) * 50
            
            # Determine color based on sentiment
            if sentiment_label.lower() == 'positive':
                color = "#28a745"  # Green for positive
            elif sentiment_label.lower() == 'negative':
                color = "#dc3545"  # Red for negative
            else:
                color = "#6c757d"  # Gray for neutral
                
            st.markdown(f"Sentiment: {sentiment_label}")
            st.progress(sentiment_percentage / 100)
            
            # Show emoji based on sentiment
            emoji = "😐"  # Neutral face
            if sentiment_score > 0.5:
                emoji = "😄"  # Very happy
            elif sentiment_score > 0.25:
                emoji = "😊"  # Happy
            elif sentiment_score < -0.5:
                emoji = "😠"  # Very sad
            elif sentiment_score < -0.25:
                emoji = "☹️"  # Sad
                
            st.markdown(f"<span style='font-size: 2rem;'>{emoji}</span>", unsafe_allow_html=True)
        
        # Display sentiment highlights if available
        highlights = sentiment.get('highlights', {})
        if highlights and (highlights.get('most_positive') or highlights.get('most_negative')):
            st.markdown("#### Sentiment Highlights")
            highlight_cols = st.columns(2)
            
            with highlight_cols[0]:
                st.markdown("**Most Positive**")
                if highlights.get('most_positive'):
                    st.markdown(f"<div style='background-color: rgba(40, 167, 69, 0.1); padding: 10px; border-radius: 5px; border-left: 4px solid #28a745;'>\"{highlights['most_positive']}\"</div>", unsafe_allow_html=True)
                else:
                    st.caption("No significant positive sentiment detected")
                    
            with highlight_cols[1]:
                st.markdown("**Most Negative**")
                if highlights.get('most_negative'):
                    st.markdown(f"<div style='background-color: rgba(220, 53, 69, 0.1); padding: 10px; border-radius: 5px; border-left: 4px solid #dc3545;'>\"{highlights['most_negative']}\"</div>", unsafe_allow_html=True)
                else:
                    st.caption("No significant negative sentiment detected")
        
        # Display any additional sentiment stats if available
        if 'stats' in sentiment:
            stats = sentiment['stats']
            st.caption(f"Positive words: {stats.get('positive_words', 0)} | Negative words: {stats.get('negative_words', 0)} | Total analyzed: {stats.get('total_analyzed', 0)} | Paragraphs: {stats.get('paragraphs_analyzed', 0)}")
        
        # Key Phrases section
        st.markdown("### 🗝️ Key Phrases")
        key_phrases = result['analysis'].get('key_phrases', [])
        
        if key_phrases:
            # Create a formatted display for key phrases
            for phrase_data in key_phrases:
                if isinstance(phrase_data, dict):
                    phrase = phrase_data.get('phrase', '')
                    score = phrase_data.get('score', 0)
                    context = phrase_data.get('context', '')
                    
                    # Create an expander for each phrase
                    with st.expander(f"{phrase} (Score: {score})"):
                        if context:
                            # Highlight the phrase in the context
                            highlighted_context = context.replace(phrase, f"**{phrase}**")
                            st.markdown(highlighted_context)
                else:
                    # Simple string format
                    st.markdown(f"- {phrase_data}")
        else:
            st.info("No key phrases identified.")
        
        # Topics section
        st.markdown("### 🗂️ Topics")
        topics = result['analysis'].get('topics', [])
        
        if topics:
            # Create columns to display topics
            topic_cols = st.columns(2)
            
            for i, topic_data in enumerate(topics):
                col_index = i % 2
                
                with topic_cols[col_index]:
                    if isinstance(topic_data, dict):
                        category = topic_data.get('category', '').title()
                        score = topic_data.get('score', 0)
                        keywords = topic_data.get('keywords', [])
                        
                        # Create a card-like display
                        st.markdown(f"**{category}**")
                        st.progress(min(score / 100, 1.0))  # Normalize score to 0-1 range
                        st.caption(f"Score: {score}")
                        
                        if keywords:
                            st.markdown("Keywords: " + ", ".join(keywords))
                    else:
                        # Simple string format
                        st.markdown(f"- {topic_data}")
        else:
            st.info("No topics identified.")
    
    with legal_tab:
        # Risk Factors section
        st.markdown("### ⚠️ Risk Factors")
        risks = result['analysis'].get('risk_factors', [])
        if risks:
            for i, risk in enumerate(risks):
                severity = risk.get('severity', 'medium')
                severity_color = {
                    'high': '#FF4B4B',  # Red for high severity
                    'medium': '#F59E0B',  # Amber for medium severity
                    'low': '#10B981'  # Green for low severity
                }.get(severity.lower(), '#D3D3D3')  # Default gray
                
                st.markdown(
                    f"<div style='display: flex; align-items: center; margin-bottom: 10px;'>"
                    f"<div style='background-color: {severity_color}; width: 12px; height: 12px; border-radius: 50%; margin-right: 10px;'></div>"
                    f"<strong>{risk.get('title', 'Risk')}:</strong> {risk.get('description', 'No description')}"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No risk factors identified in this document.")
        
        # Legal Terms section
        st.markdown("### ⚖️ Legal Terms")
        legal_terms = result['analysis'].get('legal_terms', [])
        if legal_terms:
            # Group terms by normalized form to avoid duplicates
            term_groups = {}
            for term_data in legal_terms:
                if isinstance(term_data, dict):
                    normalized = term_data.get('normalized', '').lower()
                    if normalized not in term_groups:
                        term_groups[normalized] = {
                            'term': term_data.get('term', normalized),
                            'count': 1,
                            'context': term_data.get('context', '')
                        }
                    else:
                        term_groups[normalized]['count'] += 1
                else:
                    # Handle old format (plain strings)
                    term = term_data.lower()
                    if term not in term_groups:
                        term_groups[term] = {'term': term, 'count': 1, 'context': ''}
                    else:
                        term_groups[term]['count'] += 1
            
            # Sort terms by frequency
            sorted_terms = sorted(term_groups.values(), key=lambda x: x['count'], reverse=True)
            
            # Display terms in a more visual way
            cols = st.columns(3)
            for i, term_info in enumerate(sorted_terms):
                col_idx = i % 3
                
                with cols[col_idx]:
                    st.markdown(
                        f"<div style='background-color: rgba(53, 58, 75, 0.15); padding: 10px; border-radius: 5px; margin-bottom: 10px;'>"
                        f"<strong>{term_info['term']}</strong> <span style='float: right; background-color: rgba(53, 58, 75, 0.25); border-radius: 12px; padding: 2px 8px;'>{term_info['count']}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if term_info['context'] and i < 6:  # Show context for top terms only
                        with st.expander("Show context"):
                            st.caption(term_info['context'])
        else:
            st.info("No legal terms identified in this document.")
        
        # References section
        st.markdown("### 📚 References")
        references = result['analysis'].get('references', [])
        if references:
            for ref in references:
                if isinstance(ref, dict):
                    ref_type = ref.get('type', 'Reference').title()
                    ref_text = ref.get('text', '')
                    ref_source = ref.get('source', '')
                    
                    st.markdown(
                        f"<div style='border-left: 3px solid #4B5563; padding-left: 10px; margin-bottom: 10px;'>"
                        f"<strong>{ref_type}:</strong> {ref_text}"
                        f"{' <br/><span style="color: #6B7280;">Source: ' + ref_source + '</span>' if ref_source else ''}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                else:
                    # Simple string references
                    st.markdown(f"- {ref}")
        else:
            st.info("No legal references found in this document.")

# Helper functions for visualizations
def format_file_size(size_bytes):
    """Format file size from bytes to human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def get_readability_label(score):
    """Get a descriptive label for a readability score"""
    if score >= 90:
        return "Very Easy - 5th Grade"
    elif score >= 80:
        return "Easy - 6th Grade"
    elif score >= 70:
        return "Fairly Easy - 7th Grade"
    elif score >= 60:
        return "Standard - 8th-9th Grade"
    elif score >= 50:
        return "Fairly Difficult - 10th-12th Grade"
    elif score >= 30:
        return "Difficult - College"
    else:
        return "Very Difficult - College Graduate"

def get_sentiment_color(score):
    """Get appropriate color for sentiment display"""
    if score < -0.1:
        return "inverse"  # Red for negative
    elif score > 0.1:
        return "normal"   # Green for positive
    else:
        return "off"      # Gray for neutral

def create_sentiment_gauge(score):
    """Create a sentiment gauge chart using Plotly"""
    import plotly.graph_objects as go
    
    # Normalize score to 0-100 range for gauge
    normalized_score = (score + 1) * 50
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=normalized_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Sentiment"},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': get_gauge_color(score)},
            'steps': [
                {'range': [0, 30], 'color': '#FF4B4B'},  # Red for negative
                {'range': [30, 70], 'color': '#D3D3D3'},  # Gray for neutral
                {'range': [70, 100], 'color': '#4CAF50'}  # Green for positive
            ],
            'threshold': {
                'line': {'color': 'black', 'width': 3},
                'thickness': 0.75,
                'value': normalized_score
            }
        }
    ))
    
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

def get_gauge_color(score):
    """Get color for the gauge based on sentiment score"""
    if score > 0.15:
        return '#4CAF50'  # Green for positive
    elif score < -0.15:
        return '#FF4B4B'  # Red for negative
    return '#D3D3D3'  # Gray for neutral

def render_key_phrase_tags(key_phrases):
    """Display key phrases as interactive tags"""
    html_content = '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'    
    
    for phrase in key_phrases:
        # Generate a color based on the phrase (for visual variety)
        color = generate_tag_color(phrase)
        html_content += f'<div style="background-color: {color}; color: #fff; padding: 5px 10px; border-radius: 15px; font-size: 14px;">{phrase}</div>'
    
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

def generate_tag_color(text):
    """Generate a consistent color based on text content"""
    # Simple hash function to generate colors
    hash_value = sum(ord(c) for c in text) % 5
    colors = ['#3B82F6', '#10B981', '#8B5CF6', '#EC4899', '#F59E0B']
    return colors[hash_value]

def display_topics_with_importance(topics):
    """Display topics with their importance scores and descriptions"""
    for i, topic in enumerate(topics):
        with st.expander(f"{topic['topic']} (Importance: {topic['importance']:.2f})"):
            if topic.get('description'):
                st.write(topic['description'])
            else:
                st.write("No description available.")

def display_risk_factors(risks):
    """Display risk factors with severity indicators"""
    if not risks:
        st.info("No risk factors identified in this document.")
        return
        
    for risk in risks:
        severity = risk.get('severity', 'low').lower()
        severity_color = {
            'high': '#FF4B4B',  # Red for high severity
            'medium': '#F59E0B',  # Amber for medium severity
            'low': '#10B981'  # Green for low severity
        }.get(severity, '#D3D3D3')  # Default gray
        
        st.markdown(
            f"<div style='display: flex; align-items: center; margin-bottom: 10px;'>"
            f"<div style='background-color: {severity_color}; width: 12px; height: 12px; border-radius: 50%; margin-right: 10px;'></div>"
            f"<strong>{risk.get('title', 'Risk')}:</strong> {risk.get('description', 'No description')}"
            f"</div>",
            unsafe_allow_html=True
        )

def display_legal_terms(legal_terms):
    """Display legal terms with context"""
    if not legal_terms:
        st.info("No legal terms identified in this document.")
        return
        
    for term in legal_terms:
        with st.expander(f"{term['term'].title()}"):
            st.write(term.get('context', 'No context available'))

def display_references(references):
    """Display references with their types and context"""
    if not references:
        st.info("No references identified in this document.")
        return
        
    for ref in references:
        with st.expander(f"{ref['reference']} ({ref.get('type', 'Unknown')}):"):
            st.write(f"**Type:** {ref.get('type', 'Unknown')}")
            st.write(f"**Description:** {ref.get('description', 'No description')}")
            st.write(f"**Context:** {ref.get('context', 'No context available')}")

def display_compliance_check(compliance):
    """Display compliance check results as a table"""
    if not compliance:
        st.info("No compliance data available for this document.")
        return
        
    # Privacy policy elements
    if 'privacy_policy' in compliance:
        st.subheader("Privacy Policy Elements")
        privacy_elements = compliance['privacy_policy']
        
        privacy_data = []
        for element, present in privacy_elements.items():
            icon = "✅" if present else "❌"
            privacy_data.append([element.replace("_", " ").title(), icon])
        
        privacy_df = pd.DataFrame(privacy_data, columns=["Element", "Present"])
        st.dataframe(privacy_df, hide_index=True)
    
    # Contract elements
    if 'contract' in compliance:
        st.subheader("Contract Elements")
        contract_elements = compliance['contract']
        
        contract_data = []
        for element, present in contract_elements.items():
            icon = "✅" if present else "❌"
            contract_data.append([element.replace("_", " ").title(), icon])
        
        contract_df = pd.DataFrame(contract_data, columns=["Element", "Present"])
        st.dataframe(contract_df, hide_index=True)

# Main navigation
with st.sidebar:
    # Logo and title
    st.image(logo_path, width=200)
    st.markdown("### LEGALe TROY")
    st.markdown("<div class='brand-tag'>AI-BASED LEGAL-TECH</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    nav_selection = st.radio(
        label="Navigation",
        options=["Upload Document", "View Documents", "Document Comparison"],
        label_visibility="visible"
    )

# Main content
if nav_selection == "Upload Document":
    upload_document()
elif nav_selection == "View Documents":
    view_documents()
else:  # Document Comparison
    st.header("Document Comparison", divider="blue")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("First Document")
        doc1 = st.file_uploader(
            label="Upload first document",
            type=["pdf", "doc", "docx", "txt"],
            key="doc1_upload",
            label_visibility="visible"
        )
    
    with col2:
        st.subheader("Second Document")
        doc2 = st.file_uploader(
            label="Upload second document",
            type=["pdf", "doc", "docx", "txt"],
            key="doc2_upload",
            label_visibility="visible"
        )
    
    if doc1 and doc2:
        if st.button("Compare Documents", use_container_width=True):
            with st.spinner("Comparing documents..."):
                try:
                    # Save files temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc1.name.split('.')[-1]}") as tmp1, \
                         tempfile.NamedTemporaryFile(delete=False, suffix=f".{doc2.name.split('.')[-1]}") as tmp2:
                        tmp1.write(doc1.getvalue())
                        tmp2.write(doc2.getvalue())
                        
                        comparison = document_service.compare_documents(tmp1.name, tmp2.name)
                        
                        # Display comparison results
                        st.markdown("### Comparison Results")
                        
                        # Similarity score
                        st.metric(
                            label="Overall Similarity",
                            value=f"{comparison['similarity_score']:.1%}",
                            label_visibility="visible"
                        )
                        
                        # Content differences
                        with st.expander("Content Differences", expanded=True):
                            st.json(comparison.get("differences", {}))
                        
                        # Common elements
                        with st.expander("Common Elements"):
                            st.json(comparison.get("common_elements", {}))
                        
                        # Unique elements
                        with st.expander("Unique Elements"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"### Unique to {doc1.name}")
                                st.json(comparison.get("unique_to_first", {}))
                            with col2:
                                st.markdown(f"### Unique to {doc2.name}")
                                st.json(comparison.get("unique_to_second", {}))
                finally:
                    # Cleanup
                    try:
                        os.unlink(tmp1.name)
                        os.unlink(tmp2.name)
                    except:
                        pass

# Footer
st.markdown("---")
st.markdown(" 2025 LEGALe TROY | Powered by AI")
