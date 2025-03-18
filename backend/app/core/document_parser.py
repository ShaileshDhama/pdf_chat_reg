import os
from typing import List, Dict, Any, Optional, Tuple, Union
import re
import fitz  # PyMuPDF
import PyPDF2
import docx
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from textblob import TextBlob
import numpy as np
import json
import spacy
import langdetect
from .document_processing import DocumentProcessor

# Properly import modules with fallbacks
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    # Create mock spacy namespace
    class MockSpacy:
        def load(self, model):
            class MockNLP:
                def __call__(self, text):
                    class MockDoc:
                        class MockSent:
                            def __init__(self, text):
                                self.text = text
                        
                        def __init__(self, text):
                            self.text = text
                            self.noun_chunks = []
                            self.ents = []
                            self.sents = [self.MockSent(s) for s in text.split('.')]
                    
                    return MockDoc(text)
    spacy = MockSpacy()

# Separate try block for transformers to avoid interdependency issues
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    # Create mock transformers namespace
    class MockPipeline:
        def __call__(self, text, **kwargs):
            return [{"summary_text": "Summary not available due to missing dependencies"}]
                    
    def pipeline(*args, **kwargs):
        return MockPipeline()

# Try to import and configure OCR
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
    # Check if tesseract is accessible
    try:
        pytesseract.get_tesseract_version()
    except Exception:
        OCR_AVAILABLE = False
        print("Tesseract OCR is not properly installed or configured.")
        # Create a mock pytesseract
        class MockPytesseract:
            def image_to_string(self, *args, **kwargs):
                return "OCR unavailable: Tesseract not found"
        pytesseract = MockPytesseract()
except ImportError:
    OCR_AVAILABLE = False
    # Create mock OCR
    class MockPytesseract:
        def image_to_string(self, *args, **kwargs):
            return "OCR unavailable: pytesseract module not installed"
    pytesseract = MockPytesseract()

class DocumentParser:
    def __init__(self):
        # Initialize NLP models
        try:
            if SPACY_AVAILABLE:
                self.nlp = spacy.load("en_core_web_sm")
            else:
                # Create a basic mock if spacy is not available
                class MockNLP:
                    def __call__(self, text):
                        class MockDoc:
                            class MockSent:
                                def __init__(self, text):
                                    self.text = text
                            
                            def __init__(self, text):
                                self.text = text
                                self.noun_chunks = []
                                self.ents = []
                                self.sents = [self.MockSent(s) for s in text.split('.')]
                        
                        return MockDoc(text)
                self.nlp = MockNLP()
            
            # Initialize transformers models if available
            if TRANSFORMERS_AVAILABLE:
                try:
                    self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                    self.qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
                except Exception as e:
                    print(f"Failed to initialize transformers models: {str(e)}")
                    self.summarizer = MockPipeline()
                    self.qa_pipeline = MockPipeline()
            else:
                self.summarizer = MockPipeline()
                self.qa_pipeline = MockPipeline()
                
        except Exception as e:
            print(f"Warning: Failed to load NLP models. {str(e)}")
            # Create a basic mock as fallback
            class MockNLP:
                def __call__(self, text):
                    class MockDoc:
                        class MockSent:
                            def __init__(self, text):
                                self.text = text
                        
                        def __init__(self, text):
                            self.text = text
                            self.noun_chunks = []
                            self.ents = []
                            self.sents = [self.MockSent(s) for s in text.split('.')]
                    
                    return MockDoc(text)
            self.nlp = MockNLP()
            self.summarizer = MockPipeline()
            self.qa_pipeline = MockPipeline()
        
        # Configure OCR if available
        self.ocr_available = OCR_AVAILABLE
        
        # Configure Tesseract path if OCR is available
        if self.ocr_available and hasattr(pytesseract, 'pytesseract'):
            try:
                pytesseract.pytesseract.tesseract_cmd = r'tesseract'  # Update path if needed
            except Exception as e:
                print(f"Error configuring tesseract: {str(e)}")
                self.ocr_available = False
        
    async def parse_document(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a document and extract its content, structure, and metadata.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            A dictionary containing parsed document data including content, metadata, and structure
        """
        try:
            # Use the DocumentProcessor to process the document
            result = await DocumentProcessor.process_document(file_path)
            
            # Add additional parsing if needed
            if result["content"]:
                # Generate summary if not already present
                if not result.get("summary"):
                    try:
                        result["summary"] = self._generate_summary(result["content"])
                    except Exception as e:
                        print(f"Summary generation error: {str(e)}")
                        result["summary"] = "Summary generation failed."
                
                # Extract entities if not already present and NLP is available
                if not result["entities"] and self.nlp is not None:
                    try:
                        result["entities"] = self._extract_entities(result["content"])
                    except Exception as e:
                        print(f"Entity extraction error: {str(e)}")
                
                # Analyze structure if not already present
                if not result.get("structure"):
                    try:
                        result["structure"] = self._analyze_structure(result["content"])
                    except Exception as e:
                        print(f"Structure analysis error: {str(e)}")
                        result["structure"] = []
            
            return result
            
        except Exception as e:
            print(f"Critical parsing error: {str(e)}")
            # Return minimal structure in case of catastrophic failure
            return {
                "content": f"Error parsing document: {str(e)}",
                "pages": [{
                    "text": f"Error: {str(e)}",
                    "tables": [],
                    "images": [],
                    "blocks": []
                }],
                "metadata": {
                    "title": os.path.basename(file_path),
                    "page_count": 0,
                    "file_type": "unknown"
                },
                "tables": [],
                "images": [],
                "language": "en",
                "entities": [],
                "summary": f"Document parsing failed due to error: {str(e)}"
            }
    
    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            A dictionary containing detailed analysis results
        """
        # Parse the document first
        try:
            # First try to parse the document
            try:
                parse_result = await self.parse_document(file_path)
            except Exception as e:
                print(f"Error in document parsing phase: {str(e)}")
                # Return a minimal structure that will not break downstream processors
                return {
                    "error": f"Parsing error: {str(e)}",
                    "content": "",
                    "metadata": {
                        "title": os.path.basename(file_path),
                        "page_count": 0,
                        "file_type": os.path.splitext(file_path)[1][1:]
                    },
                    "analysis": {
                        "document_type": "unknown",
                        "key_phrases": [],
                        "readability_score": 0,
                        "sentiment": {"score": 0, "label": "neutral"},
                        "topics": [],
                        "compliance": {},
                        "risk_factors": [],
                        "legal_terms": [],
                        "references": []
                    }
                }
            
            # Perform additional analysis
            doc_type = "unknown"
            try:
                doc_type = self._detect_document_type(parse_result.get("content", ""))
            except Exception as e:
                print(f"Error detecting document type: {str(e)}")
            
            # Default analysis structure
            analysis = {
                "document_type": doc_type,
                "key_phrases": [],
                "readability_score": 0,
                "sentiment": {"score": 0, "label": "neutral"},
                "topics": [],
                "compliance": {},
                "risk_factors": [],
                "legal_terms": [],
                "references": []
            }
            
            # Only perform detailed analysis if there's content
            if parse_result.get("content"):
                try:
                    analysis["key_phrases"] = self._extract_key_phrases(parse_result["content"])
                except Exception as e:
                    print(f"Error extracting key phrases: {str(e)}")
                
                try:
                    analysis["readability_score"] = self._calculate_readability(parse_result["content"])
                except Exception as e:
                    print(f"Error calculating readability: {str(e)}")
                
                try:
                    analysis["sentiment"] = self._analyze_sentiment(parse_result["content"])
                except Exception as e:
                    print(f"Error analyzing sentiment: {str(e)}")
                
                try:
                    analysis["topics"] = self._extract_topics(parse_result["content"])
                except Exception as e:
                    print(f"Error extracting topics: {str(e)}")
                
                if doc_type == "legal":
                    try:
                        analysis["compliance"] = self._check_compliance(parse_result["content"])
                    except Exception as e:
                        print(f"Error checking compliance: {str(e)}")
                
                try:
                    analysis["risk_factors"] = self._extract_risk_factors(parse_result["content"])
                except Exception as e:
                    print(f"Error identifying risk factors: {str(e)}")
                
                try:
                    analysis["legal_terms"] = self._extract_legal_terms(parse_result["content"])
                except Exception as e:
                    print(f"Error extracting legal terms: {str(e)}")
                
                try:
                    analysis["references"] = self._extract_references(parse_result["content"])
                except Exception as e:
                    print(f"Error extracting references: {str(e)}")
            
            # Add analysis to parse result
            parse_result["analysis"] = analysis
            
            return parse_result
        except Exception as e:
            # Log the error
            print(f"Critical error in document analysis: {str(e)}")
            # Return basic structure with error
            return {
                "error": f"Analysis error: {str(e)}",
                "content": "",
                "metadata": {},
                "pages": [],
                "tables": [],
                "images": [],
                "entities": [],
                "language": "en",
                "summary": f"Analysis failed: {str(e)}",
                "analysis": {
                    "document_type": "unknown",
                    "key_phrases": [],
                    "readability_score": 0,
                    "sentiment": {"score": 0, "label": "neutral"},
                    "topics": [],
                    "compliance": {},
                    "risk_factors": [],
                    "legal_terms": [],
                    "references": []
                }
            }
    
    def _detect_document_type(self, text: str) -> Dict[str, Any]:
        """
        Detect the type of legal document based on content analysis.
        
        Args:
            text: The document text to analyze
            
        Returns:
            Dict with document type information including:
            - document_type: Main document category
            - sub_type: More specific document classification
            - confidence: Confidence score (0-1)
            - indicators: List of keywords/phrases that indicated the document type
        """
        if not text or len(text.strip()) < 100:
            return {
                "document_type": "Unknown",
                "sub_type": None,
                "confidence": 0.0,
                "indicators": []
            }
        
        # Normalize text for analysis
        text_lower = text.lower()
        text_lines = [line.strip() for line in text.split("\n") if line.strip()]
        title_text = " ".join(text_lines[:10]).lower()  # First few lines are often titles
        
        # Define document types with their indicators
        document_types = [
            {
                "type": "Contract",
                "sub_types": [
                    {"name": "Non-Disclosure Agreement", "indicators": ["non-disclosure", "nda", "confidentiality agreement", "confidential information", "proprietary information", "trade secret"]},
                    {"name": "Employment Contract", "indicators": ["employment agreement", "employment contract", "offer of employment", "terms of employment", "job offer"]},
                    {"name": "Service Agreement", "indicators": ["service agreement", "consulting agreement", "professional services", "statement of work", "scope of services"]},
                    {"name": "License Agreement", "indicators": ["license agreement", "software license", "end user license", "eula", "licensing terms"]},
                    {"name": "Purchase Agreement", "indicators": ["purchase agreement", "sale agreement", "purchase contract", "asset purchase", "stock purchase"]},
                    {"name": "Rental Agreement", "indicators": ["lease agreement", "rental contract", "tenancy agreement", "lease terms", "property rental"]},
                    {"name": "General Contract", "indicators": ["agreement", "contract", "terms and conditions", "obligations", "parties"]} 
                ]
            },
            {
                "type": "Policy",
                "sub_types": [
                    {"name": "Privacy Policy", "indicators": ["privacy policy", "privacy notice", "personal information", "data collection", "information we collect"]},
                    {"name": "Terms of Service", "indicators": ["terms of service", "terms of use", "user agreement", "terms and conditions", "acceptable use"]},
                    {"name": "Cookie Policy", "indicators": ["cookie policy", "cookie notice", "use of cookies", "tracking technologies", "browser cookies"]},
                    {"name": "Security Policy", "indicators": ["security policy", "information security", "data security", "security practices", "security measures"]},
                    {"name": "Return Policy", "indicators": ["return policy", "refund policy", "exchange policy", "return procedure", "money back"]},
                    {"name": "Company Policy", "indicators": ["company policy", "corporate policy", "policy statement", "policy document", "guidelines"]}
                ]
            },
            {
                "type": "Corporate Document",
                "sub_types": [
                    {"name": "Articles of Incorporation", "indicators": ["articles of incorporation", "certificate of incorporation", "corporate charter", "articles of organization", "incorporation document"]},
                    {"name": "Bylaws", "indicators": ["bylaws", "company bylaws", "corporate bylaws", "bylaws of", "organizational bylaws"]},
                    {"name": "Board Resolution", "indicators": ["board resolution", "corporate resolution", "resolution of", "resolved that", "board of directors"]},
                    {"name": "Shareholder Agreement", "indicators": ["shareholder agreement", "shareholders agreement", "stockholder agreement", "equity holders", "share transfer"]},
                    {"name": "Annual Report", "indicators": ["annual report", "financial report", "yearly report", "fiscal year", "financial statements"]},
                    {"name": "Corporate Minutes", "indicators": ["meeting minutes", "corporate minutes", "minutes of the meeting", "board meeting", "proceedings of"]}
                ]
            },
            {
                "type": "Legal Filing",
                "sub_types": [
                    {"name": "Complaint", "indicators": ["complaint", "plaintiff", "defendant", "jurisdiction", "cause of action"]},
                    {"name": "Motion", "indicators": ["motion", "moves the court", "memorandum", "relief", "order"]},
                    {"name": "Brief", "indicators": ["brief", "argument", "citation", "authority", "respectfully submitted"]},
                    {"name": "Affidavit", "indicators": ["affidavit", "sworn statement", "under penalty of perjury", "personally appeared", "depose and say"]},
                    {"name": "Subpoena", "indicators": ["subpoena", "commanded to appear", "testimony", "witness", "evidence"]},
                    {"name": "Settlement Agreement", "indicators": ["settlement agreement", "release of claims", "dispute resolution", "settlement terms", "full and final settlement"]}
                ]
            },
            {
                "type": "Regulatory Document",
                "sub_types": [
                    {"name": "Data Protection Agreement", "indicators": ["data processing agreement", "data protection", "gdpr", "data controller", "data processor"]},
                    {"name": "Compliance Report", "indicators": ["compliance report", "compliance assessment", "regulatory compliance", "compliance review", "compliance audit"]},
                    {"name": "Tax Document", "indicators": ["tax return", "tax form", "tax statement", "tax filing", "income tax"]},
                    {"name": "Regulatory Filing", "indicators": ["regulatory filing", "sec filing", "form 10-", "regulation", "compliance filing"]}
                ]
            },
            {
                "type": "Estate Document",
                "sub_types": [
                    {"name": "Will", "indicators": ["last will and testament", "testator", "bequeath", "devise", "executor"]},
                    {"name": "Trust", "indicators": ["trust agreement", "trust document", "trustee", "beneficiary", "trust property"]},
                    {"name": "Power of Attorney", "indicators": ["power of attorney", "attorney-in-fact", "agent", "principal", "authorize and empower"]},
                    {"name": "Living Will", "indicators": ["living will", "advance directive", "healthcare directive", "medical decisions", "life-sustaining treatment"]}
                ]
            },
            {
                "type": "Intellectual Property",
                "sub_types": [
                    {"name": "Patent Application", "indicators": ["patent application", "invention", "claim", "prior art", "patent no"]},
                    {"name": "Trademark Registration", "indicators": ["trademark registration", "trademark application", "mark", "goods and services", "trademark class"]},
                    {"name": "Copyright Registration", "indicators": ["copyright registration", "copyright notice", "all rights reserved", "creative work", "author"]},
                    {"name": "IP Assignment", "indicators": ["intellectual property assignment", "ip assignment", "assign rights", "transfer of rights", "assign and transfer"]}
                ]
            }
        ]
        
        # Check for document type matches
        best_match = {"type": "Unknown Document", "sub_type": None, "confidence": 0.0, "indicators": []}
        
        for doc_category in document_types:
            for sub_type in doc_category["sub_types"]:
                indicators_found = []
                for indicator in sub_type["indicators"]:
                    if indicator in text_lower:
                        indicators_found.append(indicator)
                
                if indicators_found:
                    # Calculate confidence based on number of indicators found
                    confidence = min(0.3 + (len(indicators_found) / len(sub_type["indicators"])) * 0.7, 1.0)
                    
                    # Boost confidence if indicators appear in title
                    title_indicators = [ind for ind in indicators_found if ind in title_text]
                    if title_indicators:
                        confidence = min(confidence + 0.2, 1.0)
                    
                    # Update best match if this is better
                    if confidence > best_match["confidence"]:
                        best_match = {
                            "type": doc_category["type"],
                            "sub_type": sub_type["name"],
                            "confidence": confidence,
                            "indicators": indicators_found
                        }
        
        # Format the result
        return {
            "document_type": best_match["type"], 
            "sub_type": best_match["sub_type"],
            "confidence": best_match["confidence"],
            "indicators": best_match["indicators"]
        }
    
    def _extract_key_phrases(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key phrases from the document using TF-IDF approach combined with POS tagging.
        """
        try:
            if not text or not text.strip():
                return []
            
            # Clean text and tokenize
            cleaned_text = re.sub(r'[^\w\s.]', ' ', text.lower())
            sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s|\n', cleaned_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            if not sentences:
                return []
            
            # Remove stopwords
            stop_words = {
                'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when',
                'where', 'how', 'to', 'of', 'for', 'with', 'in', 'on', 'by', 'from', 'up', 'about',
                'into', 'over', 'after', 'be', 'is', 'am', 'are', 'was', 'were', 'been', 'being',
                'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'can', 'could',
                'should', 'would', 'might', 'must', 'shall', 'will', 'may', 'that', 'which', 'who',
                'whom', 'whose', 'this', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
                'we', 'us', 'our', 'i', 'me', 'my', 'mine', 'you', 'your', 'yours', 'he', 'she',
                'him', 'her', 'his', 'hers', 'at', 'so', 'such', 'than', 'too', 'very'
            }
            
            # Generate candidate phrases (noun phrases and key words)
            phrases = []
            
            for sentence in sentences:
                words = [w for w in sentence.split() if w.strip() and w not in stop_words]
                
                # Find potential phrases (2-4 words)
                for i in range(len(words)):
                    for n in range(1, min(5, len(words) - i + 1)):
                        phrase = ' '.join(words[i:i+n])
                        if len(phrase) > 3:  # Minimum length of meaningful phrases
                            phrases.append(phrase)
            
            # Calculate frequency of each phrase
            phrase_freq = {}
            for phrase in phrases:
                if phrase in phrase_freq:
                    phrase_freq[phrase] += 1
                else:
                    phrase_freq[phrase] = 1
            
            # Filter phrases by frequency
            min_freq = 1 if len(phrases) < 100 else 2  # Adjust based on document length
            filtered_phrases = {phrase: freq for phrase, freq in phrase_freq.items() if freq >= min_freq}
            
            # Score phrases by frequency, length, and word importance
            scored_phrases = []
            for phrase, freq in filtered_phrases.items():
                # Score based on phrase length (favor phrases with 2-3 words)
                word_count = len(phrase.split())
                length_score = 1.0 if 2 <= word_count <= 3 else 0.8
                
                # Score based on position (phrases appearing early get higher weight)
                position_score = 0
                for i, sentence in enumerate(sentences[:10]):  # Check first 10 sentences
                    if phrase in sentence:
                        position_score = max(position_score, (10 - i) / 10)
                
                # Calculate final score
                score = freq * length_score * (1 + position_score)
                
                # Add to scored phrases
                scored_phrases.append({
                    "phrase": phrase,
                    "score": score,
                    "frequency": freq
                })
            
            # Sort by score and take top phrases
            scored_phrases.sort(key=lambda x: x["score"], reverse=True)
            top_phrases = scored_phrases[:15]  # Limit to 15 phrases
            
            # Format result
            result = []
            for item in top_phrases:
                # Find an occurrence in the text to get context
                phrase = item["phrase"]
                start_pos = text.lower().find(phrase)
                
                if start_pos >= 0:
                    # Get context around the phrase
                    context_start = max(0, start_pos - 40)
                    context_end = min(len(text), start_pos + len(phrase) + 40)
                    context = text[context_start:context_end].replace('\n', ' ').strip()
                    
                    result.append({
                        "phrase": phrase.title(),  # Capitalize phrase for display
                        "score": round(item["score"], 2),
                        "context": context
                    })
            
            return result
        
        except Exception as e:
            print(f"Error in key phrase extraction: {str(e)}")
            return []
    
    def _calculate_readability(self, text: str) -> Dict[str, Any]:
        """
        Calculate readability score using the Flesch Reading Ease formula and other metrics.
        Returns comprehensive readability metrics including:
        - Flesch Reading Ease Score
        - Average sentence length
        - Average syllables per word
        - Estimated reading time
        - Readability level category
        
        Score interpretation:
        90-100: Very Easy
        80-89: Easy
        70-79: Fairly Easy
        60-69: Standard
        50-59: Fairly Difficult
        30-49: Difficult
        0-29: Very Difficult
        """
        if not text or not text.strip():
            return {
                "score": 0.0,
                "level": "Not Available",
                "avg_sentence_length": 0,
                "avg_syllables_per_word": 0,
                "reading_time_minutes": 0,
                "word_count": 0,
                "sentence_count": 0
            }
        
        # Split text into sentences
        # This regex handles more sentence-ending punctuation and special cases
        sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s|\n', text)
        
        # Filter out empty sentences
        sentences = [s for s in sentences if s.strip()]
        
        # More accurate word extraction (handles contractions, hyphenated words better)
        words = re.findall(r'\b\w+\b', text.lower())
        
        if not sentences or not words:
            return {
                "score": 0.0,
                "level": "Not Available",
                "avg_sentence_length": 0,
                "avg_syllables_per_word": 0,
                "reading_time_minutes": 0,
                "word_count": 0,
                "sentence_count": 0
            }
        
        # Count syllables with improved method
        syllable_count = 0
        for word in words:
            syllable_count += self._count_syllables(word)
        
        # Calculate metrics
        word_count = len(words)
        sentence_count = len(sentences)
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count
        
        # Calculate Flesch Reading Ease Score
        # Formula: 206.835 - 1.015 * (words/sentences) - 84.6 * (syllables/words)
        readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Clamp score to 0-100 range
        readability_score = max(0, min(100, readability_score))
        readability_score = round(readability_score, 1)
        
        # Determine readability level
        if readability_score >= 90:
            level = "Very Easy"
        elif readability_score >= 80:
            level = "Easy"
        elif readability_score >= 70:
            level = "Fairly Easy"
        elif readability_score >= 60:
            level = "Standard"
        elif readability_score >= 50:
            level = "Fairly Difficult"
        elif readability_score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"
        
        # Estimate reading time (average adult reads ~250 words per minute)
        reading_time = word_count / 250
        
        # Compile comprehensive result
        return {
            "score": readability_score,
            "level": level,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "avg_syllables_per_word": round(avg_syllables_per_word, 2),
            "reading_time_minutes": round(reading_time, 1),
            "word_count": word_count,
            "sentence_count": sentence_count
        }
    
    def _count_syllables(self, word: str) -> int:
        """
        Count the number of syllables in a word using improved heuristics.
        """
        # Remove trailing punctuation and numbers
        word = re.sub(r'[^a-zA-Z\-]', '', word.lower().strip())
        if not word:
            return 0
            
        # Handle common exceptions
        exceptions = {
            # One syllable words that might be counted as two
            'are': 1, 'ore': 1, 'our': 1, 'sure': 1, 'were': 1, 'your': 1,
            # Words ending with silent 'e'
            'come': 1, 'some': 1, 'done': 1, 'give': 1, 'have': 1, 'live': 1, 'love': 1,
            # Words with unusual syllable patterns
            'business': 2, 'wednesday': 3, 'february': 4, 'library': 3, 'secretary': 4,
            'area': 2, 'idea': 2, 'korea': 2, 'guinea': 2, 'people': 2,
            # Legal-specific terms with standardized pronunciation
            'plaintiff': 2, 'defendant': 3, 'appeal': 2, 'court': 1, 'judge': 1,
            'jury': 2, 'attorney': 3, 'counsel': 2, 'witness': 2, 'evidence': 3,
            'affidavit': 4, 'deposition': 4, 'testimony': 4, 'verdict': 2
        }
        
        if word in exceptions:
            return exceptions[word]
        
        # Handle hyphenated words
        if '-' in word:
            return sum(self._count_syllables(part) for part in word.split('-'))
        
        # Handle contractions
        if "'" in word:
            parts = word.split("'")
            return self._count_syllables(parts[0]) + (0 if parts[1] in ['s', 'd', 'll', 't', 'm', 've', 're'] else self._count_syllables(parts[1]))
        
        # Specialized rules
        # Remove trailing 'e' as it's often silent
        if word.endswith('e') and len(word) > 2:
            word = word[:-1]
        
        # Count vowel groups
        count = 0
        prev_is_vowel = False
        vowels = 'aeiouy'
        
        for i, char in enumerate(word):
            is_vowel = char in vowels
            
            # Count vowel groups (consecutive vowels count as one syllable)
            if is_vowel and not prev_is_vowel:
                count += 1
            
            # Handle special cases with 'y'
            # 'y' at the end of a word usually forms a syllable if preceded by a consonant
            if char == 'y' and i == len(word) - 1 and i > 0 and word[i-1] not in vowels:
                if not prev_is_vowel:  # Only count if we haven't already counted this vowel group
                    count += 1
            
            prev_is_vowel = is_vowel
        
        # Special rule for -le, -les endings which often form their own syllable
        if len(word) > 2 and word.endswith('le') and word[-3] not in vowels:
            count += 1
        elif len(word) > 3 and word.endswith('les') and word[-4] not in vowels:
            count += 1
        
        # Ensure at least one syllable
        return max(1, count)
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes sentiment of the document with detailed scoring, section analysis, and key section extraction.
        
        Returns:
            Dict with overall sentiment score, breakdown by sections, key sections identified, and a summary.
        """
        if not text or not text.strip():
            return {
                "overall": {"score": 0, "label": "neutral", "confidence": 0},
                "breakdown": [],
                "key_sections": [],
                "summary": "No text provided for sentiment analysis"
            }
        
        try:
            # 1. Text pre-processing
            # Truncate text if it's very long for performance reasons
            text_to_analyze = text[:100000] if len(text) > 100000 else text
            
            # 2. Split text into logical sections for detailed analysis
            sections = self._split_text_into_sections(text_to_analyze)
            
            # 3. Sentiment scoring approach
            # Define sentiment words and their scores
            positive_terms = {
                # Strong positive terms (score: 2.0)
                "excellent": 2.0, "outstanding": 2.0, "exceptional": 2.0, "superb": 2.0, "fantastic": 2.0,
                "extraordinary": 2.0, "remarkable": 2.0, "superior": 2.0, "ideal": 2.0, "perfect": 2.0,
                "exemplary": 2.0, "wonderful": 2.0, "brilliant": 2.0, "stellar": 2.0, "magnificent": 2.0,
                
                # Medium positive terms (score: 1.5)
                "good": 1.5, "favorable": 1.5, "positive": 1.5, "beneficial": 1.5, "advantageous": 1.5,
                "satisfactory": 1.5, "effective": 1.5, "efficient": 1.5, "valuable": 1.5, "useful": 1.5,
                "successful": 1.5, "impressive": 1.5, "commendable": 1.5, "praiseworthy": 1.5,
                
                # Mild positive terms (score: 1.0)
                "adequate": 1.0, "acceptable": 1.0, "sufficient": 1.0, "reasonable": 1.0, "fair": 1.0,
                "decent": 1.0, "appropriate": 1.0, "suitable": 1.0, "fine": 1.0, "solid": 1.0,
                "capable": 1.0, "competent": 1.0, "proficient": 1.0, "skilled": 1.0, "qualified": 1.0,
                
                # Positive agreement terms (score: 1.0)
                "agree": 1.0, "consent": 1.0, "accept": 1.0, "approve": 1.0, "support": 1.0,
                "endorse": 1.0, "confirm": 1.0, "validate": 1.0, "affirm": 1.0, "authorize": 1.0,
                "honor": 1.0, "respect": 1.0, "uphold": 1.0, "maintain": 1.0, "preserve": 1.0,
                
                # Positive outcome terms (score: 1.5)
                "benefit": 1.5, "advantage": 1.5, "gain": 1.5, "improve": 1.5, "enhance": 1.5,
                "strengthen": 1.5, "boost": 1.5, "augment": 1.5, "increase": 1.2, "grow": 1.2,
                "develop": 1.2, "advance": 1.2, "progress": 1.2, "excel": 1.5, "thrive": 1.5
            }
            
            negative_terms = {
                # Strong negative terms (score: -2.0)
                "terrible": -2.0, "horrible": -2.0, "dreadful": -2.0, "awful": -2.0, "abysmal": -2.0,
                "disastrous": -2.0, "catastrophic": -2.0, "atrocious": -2.0, "appalling": -2.0, "deplorable": -2.0,
                "unacceptable": -2.0, "intolerable": -2.0, "egregious": -2.0, "outrageous": -2.0, "heinous": -2.0,
                
                # Medium negative terms (score: -1.5)
                "bad": -1.5, "poor": -1.5, "unfavorable": -1.5, "negative": -1.5, "detrimental": -1.5,
                "harmful": -1.5, "adverse": -1.5, "deficient": -1.5, "substandard": -1.5, "inferior": -1.5,
                "inadequate": -1.5, "unsatisfactory": -1.5, "disappointing": -1.5, "troubling": -1.5,
                
                # Mild negative terms (score: -1.0)
                "mediocre": -1.0, "unreasonable": -1.0, "lacking": -1.0, "defective": -1.0, "flawed": -1.0,
                "problematic": -1.0, "questionable": -1.0, "concerning": -1.0, "worrisome": -1.0, "doubtful": -1.0,
                "uncertain": -1.0, "ambiguous": -1.0, "vague": -1.0, "insufficient": -1.0,
                
                # Negative obligation terms (score: -1.0)
                "violation": -1.0, "breach": -1.0, "infringement": -1.0, "contravention": -1.0, "failure": -1.0,
                "neglect": -1.0, "negligence": -1.0, "misconduct": -1.0, "malfeasance": -1.0, "misfeasance": -1.0,
                "non-compliance": -1.0, "dereliction": -1.0, "delinquency": -1.0, "offense": -1.0, "wrongdoing": -1.0,
                
                # Restrictive terms (score: -0.8)
                "prohibit": -0.8, "forbid": -0.8, "restrict": -0.8, "limit": -0.8, "constrain": -0.8,
                "restrain": -0.8, "hinder": -0.8, "impede": -0.8, "obstruct": -0.8, "block": -0.8,
                "prevent": -0.8, "preclude": -0.8, "disallow": -0.8, "deny": -0.8, "reject": -0.8
            }
            
            # Contextual terms whose meaning depends on surrounding words
            contextual_terms = {
                "liability": {
                    "negative_context": ["unlimited", "increased", "significant", "extend"],
                    "positive_context": ["limited", "no", "reduced", "protect", "against"],
                    "negative_score": -1.0,
                    "positive_score": 1.0
                },
                "terminate": {
                    "negative_context": ["immediate", "unilateral", "without cause", "penalty"],
                    "positive_context": ["mutual", "agreement", "notice", "reasonable"],
                    "negative_score": -1.0,
                    "positive_score": 0.5
                },
                "confidential": {
                    "negative_context": ["breach", "disclosure", "unauthorized", "violation"],
                    "positive_context": ["protect", "maintain", "secure", "safeguard"],
                    "negative_score": -1.0,
                    "positive_score": 1.0
                },
                "obligation": {
                    "negative_context": ["onerous", "burdensome", "excessive", "unreasonable"],
                    "positive_context": ["fair", "reasonable", "mutual", "balanced"],
                    "negative_score": -1.0,
                    "positive_score": 0.8
                }
            }
            
            # Intensifiers and dampeners
            intensifiers = {
                "very": 1.5, "extremely": 2.0, "highly": 1.8, "particularly": 1.5, "especially": 1.5,
                "significantly": 1.7, "substantially": 1.7, "considerably": 1.6, "notably": 1.5,
                "remarkably": 1.8, "exceptionally": 1.9, "undoubtedly": 1.5, "absolutely": 1.8,
                "definitely": 1.5, "unquestionably": 1.7, "truly": 1.5, "incredibly": 1.8
            }
            
            dampeners = {
                "somewhat": 0.7, "slightly": 0.6, "relatively": 0.7, "fairly": 0.8, "rather": 0.8,
                "moderately": 0.7, "comparatively": 0.8, "reasonably": 0.8, "partially": 0.6,
                "nominally": 0.5, "marginally": 0.4, "arguably": 0.7, "presumably": 0.8,
                "apparently": 0.7, "seemingly": 0.7, "ostensibly": 0.7, "questionably": 0.6
            }
            
            # Negations
            negations = ["not", "no", "never", "neither", "nor", "none", "nothing", "nowhere", "hardly", 
                       "scarcely", "barely", "doesn't", "isn't", "wasn't", "shouldn't", "wouldn't", 
                       "couldn't", "won't", "can't", "don't", "without"]
            
            # 4. Analyze each section and track scores
            section_analysis = []
            overall_score_sum = 0.0
            overall_score_count = 0
            
            # Dictionary to track sentence score frequencies for confidence calculation
            score_distribution = {}
            
            for section in sections:
                # Skip empty sections
                if not section.strip():
                    continue
                
                # Split section into sentences for granular analysis
                sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s', section)
                sentences = [s.strip() for s in sentences if s.strip()]
                
                section_score_sum = 0.0
                section_scores = []
                
                for sentence in sentences:
                    sentence_lower = sentence.lower()
                    words = re.findall(r'\b\w+\b', sentence_lower)
                    
                    # Check for negations first
                    negation_present = False
                    for neg in negations:
                        if neg in words:
                            negation_present = True
                            break
                    
                    sentence_score = 0.0
                    matched_terms = []
                    
                    # Check for positive/negative terms
                    for word in words:
                        # Check positive terms
                        if word in positive_terms:
                            score = positive_terms[word] * (-1 if negation_present else 1)
                            sentence_score += score
                            matched_terms.append(word)
                        
                        # Check negative terms
                        elif word in negative_terms:
                            score = negative_terms[word] * (-1 if negation_present else 1)
                            sentence_score += score
                            matched_terms.append(word)
                        
                        # Check intensifiers/dampeners
                        elif word in intensifiers or word in dampeners:
                            continue  # We'll handle these in a second pass
                    
                    # Handle intensifiers/dampeners and check for their effect on sentiment terms
                    for i, word in enumerate(words):
                        if word in intensifiers and i < len(words) - 1:
                            next_word = words[i + 1]
                            if next_word in positive_terms or next_word in negative_terms:
                                multiplier = intensifiers[word]
                                if next_word in positive_terms:
                                    # Adjust the previously added score by removing it and adding the intensified version
                                    original_score = positive_terms[next_word] * (-1 if negation_present else 1)
                                    intensified_score = original_score * multiplier
                                    sentence_score = sentence_score - original_score + intensified_score
                                elif next_word in negative_terms:
                                    original_score = negative_terms[next_word] * (-1 if negation_present else 1)
                                    intensified_score = original_score * multiplier
                                    sentence_score = sentence_score - original_score + intensified_score
                        
                        elif word in dampeners and i < len(words) - 1:
                            next_word = words[i + 1]
                            if next_word in positive_terms or next_word in negative_terms:
                                multiplier = dampeners[word]
                                if next_word in positive_terms:
                                    original_score = positive_terms[next_word] * (-1 if negation_present else 1)
                                    dampened_score = original_score * multiplier
                                    sentence_score = sentence_score - original_score + dampened_score
                                elif next_word in negative_terms:
                                    original_score = negative_terms[next_word] * (-1 if negation_present else 1)
                                    dampened_score = original_score * multiplier
                                    sentence_score = sentence_score - original_score + dampened_score
                    
                    # Check contextual terms
                    for term, context_data in contextual_terms.items():
                        if term in sentence_lower:
                            # Check for negative context
                            negative_context_found = False
                            for neg_ctx in context_data["negative_context"]:
                                if neg_ctx in sentence_lower:
                                    sentence_score += context_data["negative_score"] * (-1 if negation_present else 1)
                                    negative_context_found = True
                                    matched_terms.append(f"{term} ({neg_ctx})")
                                    break
                            
                            # Check for positive context if no negative context was found
                            if not negative_context_found:
                                for pos_ctx in context_data["positive_context"]:
                                    if pos_ctx in sentence_lower:
                                        sentence_score += context_data["positive_score"] * (-1 if negation_present else 1)
                                        matched_terms.append(f"{term} ({pos_ctx})")
                                        break
                    
                    # Normalize sentence score
                    if matched_terms:
                        # Ensure the score is between -1 and 1 for this sentence
                        if sentence_score > 0:
                            normalized_score = min(1.0, sentence_score / len(matched_terms))
                        else:
                            normalized_score = max(-1.0, sentence_score / len(matched_terms))
                        
                        section_score_sum += normalized_score
                        section_scores.append(normalized_score)
                        
                        # Track score frequencies for confidence calculation
                        score_bin = round(normalized_score * 10) / 10  # Round to nearest 0.1
                        if score_bin in score_distribution:
                            score_distribution[score_bin] += 1
                        else:
                            score_distribution[score_bin] = 1
                
                # Calculate section average sentiment
                if section_scores:
                    section_avg_score = section_score_sum / len(section_scores)
                    section_label = self._get_sentiment_label(section_avg_score)
                    
                    # Calculate confidence based on score consistency in this section
                    if len(section_scores) > 1:
                        variance = sum((score - section_avg_score) ** 2 for score in section_scores) / len(section_scores)
                        confidence = max(0.0, min(1.0, 1.0 - (variance * 2)))
                    else:
                        confidence = 0.6  # Default confidence for sections with a single score
                    
                    section_analysis.append({
                        "content": section[:300] + "..." if len(section) > 300 else section,
                        "score": round(section_avg_score, 2),
                        "label": section_label,
                        "confidence": round(confidence, 2),
                        "length": len(section),
                        "matched_terms": list(set(matched_terms))[:10]  # Include top matched terms
                    })
                    
                    overall_score_sum += section_avg_score
                    overall_score_count += 1
            
            # 5. Calculate overall sentiment
            if overall_score_count > 0:
                overall_score = overall_score_sum / overall_score_count
                overall_label = self._get_sentiment_label(overall_score)
                
                # Calculate overall confidence based on distribution of scores
                if score_distribution:
                    # Confidence based on consensus - higher when more scores are clustered around the same value
                    total_scores = sum(score_distribution.values())
                    entropy = 0
                    for count in score_distribution.values():
                        probability = count / total_scores
                        entropy -= probability * math.log2(probability) if probability > 0 else 0
                    
                    # Normalize entropy (max entropy for 21 possible bins from -1.0 to 1.0 in 0.1 increments would be ~4.4)
                    max_entropy = 4.4
                    confidence = max(0.0, min(1.0, 1.0 - (entropy / max_entropy)))
                else:
                    confidence = 0.5  # Default confidence when no scores are available
            else:
                overall_score = 0.0
                overall_label = "neutral"
                confidence = 0.0
            
            # 6. Identify key sections (most positive, most negative, most extreme)
            key_sections = []
            if section_analysis:
                # Sort sections by score (ascending for negative, descending for positive)
                sorted_sections = sorted(section_analysis, key=lambda x: x["score"])
                
                # Most negative section
                if sorted_sections[0]["score"] < -0.1:
                    key_sections.append({
                        "type": "most_negative",
                        "score": sorted_sections[0]["score"],
                        "label": sorted_sections[0]["label"],
                        "content": sorted_sections[0]["content"],
                        "color": "#E53935"  # Red for negative
                    })
                
                # Most positive section
                if sorted_sections[-1]["score"] > 0.1:
                    key_sections.append({
                        "type": "most_positive",
                        "score": sorted_sections[-1]["score"],
                        "label": sorted_sections[-1]["label"],
                        "content": sorted_sections[-1]["content"],
                        "color": "#43A047"  # Green for positive
                    })
                
                # Most extreme section (furthest from neutral)
                extreme_section = max(section_analysis, key=lambda x: abs(x["score"]))
                if abs(extreme_section["score"]) > 0.3 and all(extreme_section != s for s in key_sections):
                    key_sections.append({
                        "type": "most_extreme",
                        "score": extreme_section["score"],
                        "label": extreme_section["label"],
                        "content": extreme_section["content"],
                        "color": "#FFA000" if extreme_section["score"] > 0 else "#E53935"  # Amber or red
                    })
            
            # 7. Generate overall summary
            summary = self._generate_sentiment_summary(overall_score, overall_label, section_analysis, key_sections)
            
            # 8. Create visualization data
            visualization_data = {
                "distribution": []
            }
            
            # Add score distribution data for visualization
            if score_distribution:
                for score in sorted(score_distribution.keys()):
                    visualization_data["distribution"].append({
                        "score": score,
                        "count": score_distribution[score],
                        "color": "#43A047" if score > 0 else "#E53935" if score < 0 else "#9E9E9E"  # Green, red, grey
                    })
            
            # 9. Prepare final result
            result = {
                "overall": {
                    "score": round(overall_score, 2),
                    "label": overall_label,
                    "confidence": round(confidence, 2),
                },
                "breakdown": section_analysis,
                "key_sections": key_sections,
                "summary": summary,
                "visualization": visualization_data
            }
            
            return result
            
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return {
                "overall": {"score": 0, "label": "neutral", "confidence": 0},
                "breakdown": [],
                "key_sections": [],
                "summary": f"Error occurred during sentiment analysis: {str(e)}"
            }
    
    def _get_sentiment_label(self, score: float) -> str:
        """
        Convert a sentiment score to a descriptive label.
        """
        if score >= 0.6:
            return "very positive"
        elif score >= 0.2:
            return "positive"
        elif score > -0.2:
            return "neutral"
        elif score > -0.6:
            return "negative"
        else:
            return "very negative"
    
    def _generate_sentiment_summary(self, overall_score: float, overall_label: str, 
                                 section_analysis: List[Dict[str, Any]], 
                                 key_sections: List[Dict[str, Any]]) -> str:
        """
        Generate a descriptive summary of the sentiment analysis results.
        """
        # Count positive, negative, and neutral sections
        positive_count = sum(1 for s in section_analysis if s["score"] > 0.2)
        negative_count = sum(1 for s in section_analysis if s["score"] < -0.2)
        neutral_count = len(section_analysis) - positive_count - negative_count
        
        summary_parts = []
        
        # Overall sentiment description
        if overall_score >= 0.6:
            summary_parts.append("The document has a notably positive tone overall.")
        elif overall_score >= 0.2:
            summary_parts.append("The document has a generally positive tone.")
        elif overall_score > -0.2:
            summary_parts.append("The document has a mostly neutral tone.")
        elif overall_score > -0.6:
            summary_parts.append("The document has a somewhat negative tone.")
        else:
            summary_parts.append("The document has a significantly negative tone.")
        
        # Section breakdown
        if positive_count > 0 or negative_count > 0:
            section_breakdown = f"Analysis identified {positive_count} positive section{'s' if positive_count != 1 else ''}, "
            section_breakdown += f"{negative_count} negative section{'s' if negative_count != 1 else ''}, and "
            section_breakdown += f"{neutral_count} neutral section{'s' if neutral_count != 1 else ''}."            
            summary_parts.append(section_breakdown)
        
        # Key topics or provisions sentiment
        if any(s["type"] == "most_positive" for s in key_sections):
            most_positive = next(s for s in key_sections if s["type"] == "most_positive")
            summary_parts.append(f"The document contains notably positive language regarding key topics or provisions.")
        
        if any(s["type"] == "most_negative" for s in key_sections):
            most_negative = next(s for s in key_sections if s["type"] == "most_negative")
            summary_parts.append(f"Some sections contain potentially concerning negative language.")
        
        # Combine the summary parts
        summary = " ".join(summary_parts)
        
        return summary
    
    def _split_text_into_sections(self, text: str) -> List[str]:
        """
        Split document text into logical sections for sentiment analysis.
        
        This attempts to identify structural elements like numbered sections, 
        paragraphs, or other logical divisions in the document.
        """
        if not text or not text.strip():
            return []
        
        # First try to split by numbered sections (common in legal documents)
        # Look for patterns like "1.", "Section 1.", "Article I.", etc.
        numbered_section_pattern = r'(?:\n|^)\s*(?:Section\s+|Article\s+)?(?:[0-9]{1,2}|[IVXLCDM]+)\s*\.\s+'  
        
        sections = re.split(numbered_section_pattern, text)
        
        # If we found structured sections, clean them up and return
        if len(sections) > 1:
            # Clean up sections and remove any empty ones
            sections = [s.strip() for s in sections if s.strip()]
            return sections
        
        # If no structured sections were found, split by double newlines (paragraphs)
        sections = re.split(r'\n\s*\n', text)
        sections = [s.strip() for s in sections if s.strip()]
        
        # If we have very few sections, try breaking by single newlines
        if len(sections) <= 2:
            sections = re.split(r'\n', text)
            sections = [s.strip() for s in sections if s.strip()]
        
        # If we still have very few sections, or excessively many, normalize to a reasonable number
        if len(sections) <= 2 or len(sections) > 30:
            # Try to split into approximately 10-15 equal-sized chunks
            words = text.split()
            
            if not sentences or not words:
                return []
            
            # Decide how many words per section based on total word count
            words_per_section = max(50, len(words) // 10)
            
            sections = []
            for i in range(0, len(words), words_per_section):
                section_words = words[i:i+words_per_section]
                sections.append(' '.join(section_words))
        
        return sections
    
    def _extract_topics(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract main topics from the document text using an enhanced approach combining
        TF-IDF, NER, and predefined legal categories.
        """
        try:
            if not text or not text.strip():
                return []
            
            # Truncate text for performance if very long
            text_to_analyze = text[:100000] if len(text) > 100000 else text
            
            # Clean text - remove extra whitespace and normalize
            cleaned_text = re.sub(r'\s+', ' ', text_to_analyze).strip()
            
            # Split into paragraphs for context preservation
            paragraphs = re.split(r'\n\s*\n', cleaned_text)
            paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # Define legal domain categories with their associated terms
            legal_categories = {
                "Contract Law": {
                    "terms": ["agreement", "contract", "covenant", "obligation", "party", "parties", "provision", 
                             "term", "clause", "breach", "performance", "consideration", "offer", "acceptance"],
                    "weight": 1.0,
                    "color": "#4285F4"  # Blue
                },
                "Intellectual Property": {
                    "terms": ["patent", "copyright", "trademark", "intellectual property", "ip", "invention", 
                             "author", "creator", "license", "royalty", "proprietary"],
                    "weight": 1.2,
                    "color": "#EA4335"  # Red
                },
                "Employment Law": {
                    "terms": ["employee", "employer", "employment", "work", "worker", "compensation", "salary", "wage", 
                             "termination", "fire", "hire", "discrimination", "harassment", "benefits", "leave"],
                    "weight": 0.9,
                    "color": "#FBBC05"  # Yellow
                },
                "Corporate Law": {
                    "terms": ["corporation", "company", "shareholder", "stock", "board", "director", "officer", 
                             "merger", "acquisition", "corporate", "governance", "fiduciary", "dividend", "securities"],
                    "weight": 1.1,
                    "color": "#34A853"  # Green
                },
                "Real Estate": {
                    "terms": ["property", "real estate", "land", "lease", "tenant", "landlord", "premises", 
                             "mortgage", "easement", "convey", "deed", "title", "zoning", "eviction"],
                    "weight": 0.8,
                    "color": "#8F44AD"  # Purple
                },
                "Litigation": {
                    "terms": ["lawsuit", "litigation", "dispute", "claim", "plaintiff", "defendant", "court", 
                             "judge", "jury", "complaint", "answer", "motion", "trial", "appeal", "settlement"],
                    "weight": 1.0,
                    "color": "#F4B400"  # Amber
                },
                "Privacy & Data Protection": {
                    "terms": ["privacy", "data", "personal information", "confidential", "gdpr", "ccpa", 
                               "consent", "data breach", "data protection", "disclosure", "processing"],
                    "weight": 1.3,
                    "color": "#DB4437"  # Red-orange
                },
                "Tax Law": {
                    "terms": ["tax", "taxation", "income", "deduction", "liability", "exemption", "assessment", 
                             "audit", "revenue", "withholding", "credit", "taxable", "irs", "tax return"],
                    "weight": 0.9,
                    "color": "#0F9D58"  # Green-teal
                },
                "Compliance": {
                    "terms": ["compliance", "regulation", "regulatory", "comply", "requirement", "standard", 
                             "guideline", "audit", "monitor", "enforce", "violation", "penalty", "sanction"],
                    "weight": 1.0,
                    "color": "#4285F4"  # Blue
                }
            }
            
            # These common patterns might indicate specific subject matters
            pattern_topics = {
                "agreement pattern": r'\b(this|the)\s+(agreement|contract)\b',
                "legal entity pattern": r'\b(corporation|llc|inc\.|incorporated|company|partnership|association|organization|entity|subsidiary|affiliate)\b',
                "legal action pattern": r'\b(lawsuit|litigation|claim|action|proceeding|case|trial|hearing|motion|petition|complaint|settlement|judgment|decree|order|injunction)\b',
                "date reference pattern": r'\b(dated|effective\s+date|as\s+of)\b',
                "obligation pattern": r'\b(shall|must|required\s+to|obligated\s+to)\b',
                "payment pattern": r'\b(pay|payment|compensate|remuneration|fee)\b',
                "property pattern": r'\b(property|asset|real\s+estate|building|land|premise)\b',
                "confidentiality pattern": r'\b(confidential|confidentiality|non-disclosure|nda)\b',
                "employment pattern": r'\b(employ|employee|employer|work|worker)\b',
                "ip pattern": r'\b(intellectual\s+property|patent|copyright|trademark|trade\s+secret)\b',
                "compliance pattern": r'\b(comply|compliance|regulation|law|policy|requirement)\b',
                "termination pattern": r'\b(terminate|termination|cancel|end|expir)\b',
                "dispute pattern": r'\b(dispute|disagree|arbitra|mediat)\b'
            }
            
            # Count terms by category and find pattern matches
            category_counts = {category: 0 for category in legal_categories}
            pattern_matches = {pattern: 0 for pattern in pattern_topics}
            category_contexts = {category: [] for category in legal_categories}
            term_frequencies = {category: {} for category in legal_categories}
            
            # Find exact matches for legal category terms
            for paragraph in paragraphs:
                paragraph_lower = paragraph.lower()
                
                # Check for category terms
                for category, data in legal_categories.items():
                    for term in data["terms"]:
                        term_pattern = r'\b' + re.escape(term) + r'\b'
                        matches = re.findall(term_pattern, paragraph_lower)
                        
                        if matches:
                            count = len(matches)
                            category_counts[category] += count * data["weight"]
                            
                            # Track term frequencies for this category
                            if term not in term_frequencies[category]:
                                term_frequencies[category][term] = count
                            else:
                                term_frequencies[category][term] += count
                            
                            # Store context for this category (up to 3 examples)
                            if len(category_contexts[category]) < 3:
                                # Find a sentence containing the term for better context
                                sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s', paragraph)
                                for sentence in sentences:
                                    if term in sentence.lower() and len(category_contexts[category]) < 3:
                                        # Limit context length
                                        if len(sentence) > 200:
                                            sentence = sentence[:200] + "..."
                                        if sentence not in category_contexts[category]:
                                            category_contexts[category].append(sentence)
                
                # Check for pattern matches
                for pattern_name, pattern in pattern_topics.items():
                    matches = re.findall(pattern, paragraph_lower)
                    pattern_matches[pattern_name] += len(matches)
            
            # Analyze topic patterns to boost relevant categories
            pattern_to_category_map = {
                "agreement pattern": "Contract Law",
                "legal entity pattern": "Corporate Law",
                "legal action pattern": "Litigation",
                "date reference pattern": "Contract Law",
                "obligation pattern": "Contract Law",
                "payment pattern": "Contract Law",
                "property pattern": "Real Estate",
                "confidentiality pattern": "Privacy & Data Protection",
                "employment pattern": "Employment Law",
                "ip pattern": "Intellectual Property",
                "compliance pattern": "Compliance",
                "termination pattern": "Contract Law",
                "dispute pattern": "Litigation"
            }
            
            # Boost categories based on pattern matches
            for pattern_name, count in pattern_matches.items():
                if count > 0 and pattern_name in pattern_to_category_map:
                    category = pattern_to_category_map[pattern_name]
                    category_counts[category] += count * 0.5  # Add a boost, but less than direct term matches
            
            # Extract additional potential topics using key phrase extraction
            # For simplicity, we'll use a frequency-based approach for key phrases
            words = text.split()
            
            if not sentences or not words:
                return []
            
            # Remove common stopwords
            stopwords = set(['a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when', 
                            'where', 'how', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 
                            'does', 'did', 'to', 'at', 'by', 'for', 'with', 'in', 'on', 'by', 'from', 'up', 'about', 
                            'into', 'over', 'after', 'above', 'below', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 
                            'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'all', 'any', 'both', 
                            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
                            'same', 'so', 'than', 'too', 'very', 's', 't', 'will', 'just', 'now', 'd', 'll', 'm', 'o', 
                            're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 
                            'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn', 
                            'shall', 'said', 'that', 'this', 'these', 'those', 'would', 'could', 'should', 'might', 'may', 
                            'can', 'of'])
            
            filtered_counter = {word: count for word, count in Counter(words).items() 
                              if word not in stopwords and len(word) > 3 and count > 2}
            
            # Get additional topics not covered by predefined categories
            additional_topics = []
            for word, count in sorted(filtered_counter.items(), key=lambda x: x[1], reverse=True)[:20]:
                # Check if this word is already part of a legal category
                is_in_category = False
                for category, data in legal_categories.items():
                    if any(word in term for term in data["terms"]) or \
                       any(term in word for term in data["terms"] if len(term) > 4):
                        is_in_category = True
                        break
                
                if not is_in_category and count > 5:  # Only include significant terms
                    # Find a context for this term
                    context = ""
                    for paragraph in paragraphs:
                        if word in paragraph.lower():
                            sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s', paragraph)
                            for sentence in sentences:
                                if word in sentence.lower():
                                    context = sentence[:200] + "..." if len(sentence) > 200 else sentence
                                    break
                        if context:
                            break
                    
                    additional_topics.append({
                        "topic": word.title(),
                        "score": min(100, count * 5),  # Scale the score
                        "type": "keyword",
                        "context": context,
                        "relevance": "medium" if count > 10 else "low",
                        "color": "#757575"  # Grey for additional topics
                    })
            
            # Format the main results
            topics = []
            
            # Add category-based topics
            for category, score in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                # Only include categories with meaningful scores
                if score > 3:  # Threshold to filter out noise
                    # Get top terms for this category
                    top_terms = sorted(term_frequencies[category].items(), key=lambda x: x[1], reverse=True)[:5]
                    top_terms = [term for term, count in top_terms]
                    
                    # Calculate relevance level
                    relevance = "high" if score > 20 else "medium" if score > 10 else "low"
                    
                    topics.append({
                        "topic": category,
                        "score": min(100, score * 2),  # Scale to 0-100
                        "type": "category",
                        "context": category_contexts[category][:2],  # Include up to 2 context examples
                        "top_terms": top_terms,
                        "relevance": relevance,
                        "color": legal_categories[category]["color"]
                    })
            
            # Include top additional topics that are not already covered
            topics.extend(additional_topics[:5])  # Add up to 5 additional topics
            
            # Limit to most relevant topics and sort by score
            topics = sorted(topics, key=lambda x: x["score"], reverse=True)[:10]  # Top 10 topics
            
            # Round scores for cleaner display
            for topic in topics:
                topic["score"] = round(topic["score"], 1)
            
            return topics
        
        except Exception as e:
            print(f"Error in topic extraction: {str(e)}")
            return []
    
    def _extract_legal_terms(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract legal terms from the document with categorization and context.
        Returns a list of legal terms with their categories, frequency, and context in the document.
        """
        if not text or not text.strip():
            return []
        
        # Truncate text for performance if very long
        text_to_analyze = text[:80000] if len(text) > 80000 else text
        
        try:
            # Define legal term patterns by category
            legal_term_patterns = {
                "Contract Terms": {
                    "pattern": r'\b(agreement|contract|covenant|warranty|indemnity|guarantee|undertaking|obligation|consideration|provision|clause|term|condition|binding|executed|signatory|amendment|addendum|appendix|exhibit|schedule)\b',
                    "weight": 1.0
                },
                "Legal Entities": {
                    "pattern": r'\b(corporation|llc|inc\.|incorporated|company|partnership|association|organization|entity|subsidiary|affiliate)\b',
                    "weight": 0.8
                },
                "Parties": {
                    "pattern": r'\b(party|parties|signatory|signatories|counterparty|licensor|licensee|grantor|grantee|lessor|lessee|vendor|vendee|buyer|seller)\b',
                    "weight": 0.9
                },
                "Legal Actions": {
                    "pattern": r'\b(lawsuit|litigation|claim|action|proceeding|case|trial|hearing|motion|petition|complaint|settlement|judgment|decree|order|injunction)\b',
                    "weight": 1.1
                },
                "Legal Authority": {
                    "pattern": r'\b(statute|law|regulation|code|act|bill|amendment|constitution|treaty|directive|precedent|ruling)\b',
                    "weight": 1.2
                },
                "Rights and Obligations": {
                    "pattern": r'\b(right|obligation|duty|liability|shall|must|required|prohibited|permitted|consent|approval)\b',
                    "weight": 1.0
                },
                "Property": {
                    "pattern": r'\b(property|asset|real estate|land|premises|chattel|title|deed|easement|lease|ownership)\b',
                    "weight": 0.8
                },
                "Intellectual Property": {
                    "pattern": r'\b(patent|copyright|trademark|trade secret|intellectual property|ip rights|license|royalty|proprietary)\b',
                    "weight": 1.2
                },
                "Financial Terms": {
                    "pattern": r'\b(payment|compensation|fee|expense|cost|tax|interest|penalty|damages|reimbursement|default|bankruptcy|insolvency)\b',
                    "weight": 0.9
                },
                "Time-Related Terms": {
                    "pattern": r'\b(term|period|duration|date|deadline|termination|expiration|renewal|extension|effective date)\b',
                    "weight": 0.7
                },
                "Privacy and Data": {
                    "pattern": r'\b(privacy|data|confidential|personal information|gdpr|ccpa|consent|processor|controller)\b',
                    "weight": 1.0
                },
                "Dispute Resolution": {
                    "pattern": r'\b(dispute|disagree|arbitra|mediat)\b',
                    "weight": 1.1
                },
                "Latin Legal Terms": {
                    "pattern": r'\b(de facto|de jure|bona fide|prima facie|pro rata|quid pro quo|inter alia|mutatis mutandis|pari passu|ex parte)\b',
                    "weight": 1.3
                }
            }
            
            # Find all legal terms in the document
            legal_terms_found = {}
            
            # Process sentence by sentence to maintain context
            sentences = re.split(r'(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=\.|\?|\!|\:)\s|\n', text_to_analyze)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            for sentence_idx, sentence in enumerate(sentences):
                for category, pattern_info in legal_term_patterns.items():
                    pattern = pattern_info["pattern"]
                    weight = pattern_info["weight"]
                    
                    # Find all matches in the current sentence
                    matches = re.finditer(pattern, sentence.lower())
                    
                    for match in matches:
                        term = match.group(0)
                        
                        # Create a key that combines term and category
                        term_key = f"{term}:{category}"
                        
                        if term_key in legal_terms_found:
                            legal_terms_found[term_key]["frequency"] += 1
                            
                            # Only store up to 3 context examples
                            if len(legal_terms_found[term_key]["context"]) < 3:
                                # Get context (snippet around the term)
                                context = self._extract_term_context(sentence, match.start(), match.end())
                                
                                # Highlight the term in context
                                if context not in legal_terms_found[term_key]["context"]:
                                    legal_terms_found[term_key]["context"].append(context)
                                    
                                # Note position for document relevance (terms appearing early are often more significant)
                                if sentence_idx < 5 and "document_position" not in legal_terms_found[term_key]:
                                    legal_terms_found[term_key]["document_position"] = "early"
                        else:
                            # Get context (snippet around the term)
                            context = self._extract_term_context(sentence, match.start(), match.end())
                            
                            # Create new entry
                            legal_terms_found[term_key] = {
                                "term": term,
                                "category": category,
                                "frequency": 1,
                                "weight": weight,
                                "context": [context],
                                "document_position": "early" if sentence_idx < 5 else "other"
                            }
            
            # Calculate importance score and format results
            result = []
            
            for term_key, term_data in legal_terms_found.items():
                # Calculate importance score based on frequency, weight, and position
                frequency_factor = min(10, term_data["frequency"]) / 10  # Cap at 10 occurrences for scoring
                position_factor = 1.2 if term_data.get("document_position") == "early" else 1.0
                
                importance_score = (term_data["frequency"] * term_data["weight"] * position_factor) / 2
                importance_score = min(100, importance_score)  # Cap at 100
                
                result.append({
                    "term": term_data["term"],
                    "category": term_data["category"],
                    "frequency": term_data["frequency"],
                    "importance": round(importance_score, 1),
                    "primary_context": term_data["context"][0] if term_data["context"] else "",
                    "context": term_data["context"],
                    "position": term_data.get("document_position", "other")
                })
            
            # Sort by importance score in descending order
            result = sorted(result, key=lambda x: x["importance"], reverse=True)
            
            # Limit to most important terms (up to 50)
            return result[:50]
            
        except Exception as e:
            print(f"Error extracting legal terms: {str(e)}")
            return []
    
    def _check_compliance(self, text: str) -> Dict[str, Any]:
        """
        Check document compliance with various legal and regulatory standards.
        Returns a structured assessment of compliance areas with potential issues.
        """
        if not text or not text.strip():
            return {
                "overall_status": "Not Analyzed",
                "areas": {},
                "warnings": []
            }
            
        try:
            # Get document type information
            doc_type_info = self._detect_document_type(text)
            
            # Extract key clauses from the document
            key_clauses = self._extract_key_clauses(text)
            
            # Define compliance areas and their requirements
            compliance_areas = {
                "GDPR": {
                    "keywords": ["gdpr", "general data protection regulation", "data protection", "personal data", 
                               "data subject", "data controller", "data processor", "right to erasure", "right to access"],
                    "requirements": [
                        {"name": "Consent Mechanisms", "pattern": r'\b(consent|opt.?in|permission|agree)\b.{0,50}\b(personal|data)\b', "required": True},
                        {"name": "Data Subject Rights", "pattern": r'\b(right|access|erasure|forgotten|restrict|object|portability)\b.{0,50}\b(data)\b', "required": True},
                        {"name": "Data Breach Notification", "pattern": r'\b(breach|notification|incident)\b.{0,50}\b(report|notify)\b', "required": True},
                        {"name": "Data Minimization", "pattern": r'\b(minim|necessary|proportionate|limited)\b.{0,50}\b(data|collection|processing)\b', "required": True},
                        {"name": "Lawful Basis for Processing", "pattern": r'\b(lawful|legal|legitimate|basis)\b.{0,50}\b(process|collect|data)\b', "required": True},
                        {"name": "Data Protection Officer", "pattern": r'\b(data protection officer|dpo)\b', "required": False},
                        {"name": "International Data Transfers", "pattern": r'\b(transfer|international|third country|outside)\b.{0,50}\b(data|information)\b', "required": False}
                    ],
                    "risk_level": "high",
                    "color": "#4285F4"  # Blue
                },
                "CCPA": {
                    "keywords": ["ccpa", "california consumer privacy act", "consumer privacy", "personal information", 
                               "right to delete", "right to opt-out", "right to access", "do not sell"],
                    "requirements": [
                        {"name": "Right to Know", "pattern": r'\b(right|know|access)\b.{0,50}\b(collect|personal)\b', "required": True},
                        {"name": "Right to Delete", "pattern": r'\b(right|delete|erase)\b.{0,50}\b(information|personal)\b', "required": True},
                        {"name": "Right to Opt-Out", "pattern": r'\b(opt.?out|do not sell)\b.{0,50}\b(personal|information)\b', "required": True},
                        {"name": "Notice at Collection", "pattern": r'\b(notice|disclose)\b.{0,50}\b(collect|categories|purpose)\b', "required": True},
                        {"name": "Non-Discrimination", "pattern": r'\b(discriminat|penalize|charge|deny)\b.{0,70}\b(right|request|access|delete)\b', "required": True}
                    ],
                    "risk_level": "high",
                    "color": "#EA4335"  # Red
                },
                "HIPAA": {
                    "keywords": ["hipaa", "health insurance portability", "protected health information", "phi", 
                               "medical", "health data", "health record", "patient", "healthcare"],
                    "requirements": [
                        {"name": "PHI Protection", "pattern": r'\b(protect|safeguard|secure)\b.{0,50}\b(health information|phi|medical)\b', "required": True},
                        {"name": "Authorization", "pattern": r'\b(authorization|consent|permission)\b.{0,50}\b(disclose|share|use|phi)\b', "required": True},
                        {"name": "Minimum Necessary", "pattern": r'\b(minimum necessary|need to know)\b', "required": True},
                        {"name": "Business Associate Agreement", "pattern": r'\b(business associate|baa)\b', "required": False},
                        {"name": "Breach Notification", "pattern": r'\b(breach|notification|incident)\b.{0,50}\b(report|notify)\b', "required": True}
                    ],
                    "risk_level": "high",
                    "color": "#FBBC05"  # Yellow
                },
                "Contract Completeness": {
                    "keywords": ["agreement", "contract", "terms", "parties", "signature", "obligations", "covenants"],
                    "requirements": [
                        {"name": "Party Identification", "pattern": r'\b(party|parties|between|among)\b.{0,100}\b(agreement|identified)\b', "required": True},
                        {"name": "Consideration Clause", "pattern": r'\b(consideration|payment|fee)\b.{0,100}\b(services|goods|products)\b', "required": True},
                        {"name": "Term and Termination", "pattern": r'\b(term|duration|termination)\b.{0,100}\b(agreement|contract)\b', "required": True},
                        {"name": "Governing Law", "pattern": r'\b(govern|law|jurisdiction)\b.{0,100}\b(state|country|court)\b', "required": True},
                        {"name": "Dispute Resolution", "pattern": r'\b(dispute|disagree|arbitra|mediat)\b.{0,100}\b(resolve|settlement|court)\b', "required": False},
                        {"name": "Force Majeure", "pattern": r'\b(force\s*majeure|act\s*of\s*god|beyond\s*control|unavoidable)\b', "required": False},
                        {"name": "Confidentiality", "pattern": r'\b(confidential|proprietary|non-disclosure|nda)\b', "required": False},
                        {"name": "Assignment", "pattern": r'\b(assign|transfer)\b.{0,50}\b(rights|obligations|agreement)\b', "required": False}
                    ],
                    "risk_level": "medium",
                    "color": "#34A853"  # Green
                },
                "Intellectual Property": {
                    "keywords": ["intellectual property", "ip", "patent", "copyright", "trademark", "trade secret", 
                               "license", "proprietary", "rights"],
                    "requirements": [
                        {"name": "Ownership Definition", "pattern": r'\b(own|ownership|possess|title|right)\b.{0,70}\b(ip|intellectual property|copyright|patent)\b', "required": True},
                        {"name": "License Grant", "pattern": r'\b(licens|grant|right|permission)\b.{0,70}\b(use|reproduce|modify|distribute)\b', "required": False},
                        {"name": "IP Representations", "pattern": r'\b(represent|warrant|covenant)\b.{0,70}\b(infringe|violate|ip|intellectual property)\b', "required": False},
                        {"name": "IP Indemnification", "pattern": r'\b(indemnif|defend|hold harmless)\b.{0,100}\b(infringe|claim|ip|intellectual property)\b', "required": False}
                    ],
                    "risk_level": "medium",
                    "color": "#DB4437"  # Red-orange
                },
                "Employment": {
                    "keywords": ["employment", "employee", "employer", "work", "job", "position", "salary", "wage", 
                               "compensation", "termination", "fired", "resign"],
                    "requirements": [
                        {"name": "Position Description", "pattern": r'\b(position|role|job|duties|responsibilities)\b', "required": True},
                        {"name": "Compensation", "pattern": r'\b(compensation|salary|wage|pay|payment)\b', "required": True},
                        {"name": "Working Hours", "pattern": r'\b(hours|schedule|shift|work.?time)\b', "required": True},
                        {"name": "At-Will Employment", "pattern": r'\b(at.?will|terminate|end|dismiss)\b.{0,50}\b(employment|relationship)\b', "required": False},
                        {"name": "Benefits", "pattern": r'\b(benefits|insurance|vacation|leave|pto|holiday)\b', "required": False},
                        {"name": "Non-Compete", "pattern": r'\b(non.?compete|competition|competitive|restrict)\b', "required": False}
                    ],
                    "risk_level": "medium",
                    "color": "#0F9D58"  # Green-teal
                },
                "Data Security": {
                    "keywords": ["security", "protect", "safeguard", "confidential", "encrypt", "access control", 
                               "breach", "incident", "vulnerability", "risk"],
                    "requirements": [
                        {"name": "Security Measures", "pattern": r'\b(security|protective|safeguard|measures)\b.{0,70}\b(data|information|system)\b', "required": True},
                        {"name": "Access Controls", "pattern": r'\b(access|authentication|password|credential)\b.{0,50}\b(control|restrict|limit)\b', "required": True},
                        {"name": "Encryption", "pattern": r'\b(encrypt|cipher|secure|protect)\b.{0,50}\b(data|information|transmission)\b', "required": False},
                        {"name": "Breach Response", "pattern": r'\b(breach|incident|event|compromise)\b.{0,50}\b(response|plan|notify|report)\b', "required": True}
                    ],
                    "risk_level": "high",
                    "color": "#4285F4"  # Blue
                },
                "Liability": {
                    "keywords": ["liability", "damages", "indemnification", "indemnify", "waiver", "limitation", 
                               "warranty", "disclaimer", "hold harmless"],
                    "requirements": [
                        {"name": "Limitation of Liability", "pattern": r'\b(limit|cap|restrict)\b.{0,50}\b(liability|responsible|damages)\b', "required": True},
                        {"name": "Warranty Disclaimer", "pattern": r'\b(disclaim|waive|no)\b.{0,50}\b(warrant|guarantee)\b', "required": False},
                        {"name": "Indemnification", "pattern": r'\b(indemnif|defend|hold harmless)\b', "required": False},
                        {"name": "Damages Exclusion", "pattern": r'\b(consequential|incidental|special|punitive)\b.{0,50}\b(damages|losses)\b', "required": False}
                    ],
                    "risk_level": "high",
                    "color": "#9D28AC"  # Purple
                }
            }
            
            # Check each compliance area
            compliance_results = {}
            overall_issues = []
            compliant_areas = []
            
            for area_name, area_data in compliance_areas.items():
                # First check if this area is relevant to the document
                area_relevant = False
                matched_keywords = []
                
                for keyword in area_data["keywords"]:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()):
                        area_relevant = True
                        matched_keywords.append(keyword)
                
                # Skip irrelevant areas
                if not area_relevant:
                    continue
                    
                # Check requirements for this area
                requirements_met = []
                requirements_missing = []
                requirement_contexts = {}
                
                for requirement in area_data["requirements"]:
                    # Check if the requirement pattern is found in the text
                    matches = re.finditer(requirement["pattern"], text.lower())
                    match_found = False
                    
                    for match in matches:
                        match_found = True
                        # Extract context for the match
                        match_start = max(0, match.start() - 100)
                        match_end = min(len(text_to_analyze), match.end() + 100)
                        context = text_to_analyze[match_start:match_end]
                        
                        # Add ellipsis indicators if we truncated the context
                        if match_start > 0:
                            context = "..." + context
                        if match_end < len(text_to_analyze):
                            context = context + "..."
                        
                        # Highlight the matched text
                        matched_text = text_to_analyze[match.start():match.end()]
                        context = context.replace(matched_text, f"[{matched_text}]")
                        
                        # Store the context
                        if requirement["name"] not in requirement_contexts:
                            requirement_contexts[requirement["name"]] = []
                        if len(requirement_contexts[requirement["name"]]) < 2:  # Limit to 2 context examples per requirement
                            requirement_contexts[requirement["name"]].append(context)
                    
                    if match_found:
                        requirements_met.append({
                            "name": requirement["name"],
                            "contexts": requirement_contexts.get(requirement["name"], [])
                        })
                    elif requirement["required"]:
                        requirements_missing.append(requirement["name"])
                
                # Determine compliance status for this area
                required_count = sum(1 for req in area_data["requirements"] if req["required"])
                met_required_count = sum(1 for req in requirements_met 
                                     if any(r["name"] == req["name"] and r["required"] for r in area_data["requirements"]))
                
                if required_count > 0 and met_required_count < required_count:
                    missing_ratio = (required_count - met_required_count) / required_count
                    
                    if missing_ratio > 0.5:
                        status = "Non-Compliant"
                        issue_level = "high"
                    else:
                        status = "Partially Compliant"
                        issue_level = "medium"
                    
                    overall_issues.append({
                        "area": area_name,
                        "level": issue_level,
                        "missing_requirements": requirements_missing,
                        "message": f"Missing {area_name} requirements: {', '.join(requirements_missing)}"
                    })
                else:
                    status = "Compliant"
                    compliant_areas.append(area_name)
                
                # Calculate relevance score based on keyword matches and requirements
                relevance_score = min(100, (len(matched_keywords) * 20) + (len(requirements_met) * 15))
                relevance_level = "high" if relevance_score > 70 else "medium" if relevance_score > 40 else "low"
                
                # Record detailed results for this area
                compliance_results[area_name] = {
                    "status": status,
                    "requirements_met": [req["name"] for req in requirements_met],
                    "requirements_contexts": requirement_contexts,
                    "requirements_missing": requirements_missing,
                    "relevance": relevance_level,
                    "relevance_score": relevance_score,
                    "matched_keywords": matched_keywords,
                    "risk_level": area_data["risk_level"],
                    "color": area_data["color"]
                }
            
            # Format the final results
            areas_with_issues = [{
                "name": area_name,
                "status": data["status"],
                "relevance": data["relevance"],
                "requirements_met": data["requirements_met"],
                "requirements_missing": data["requirements_missing"],
                "risk_level": data["risk_level"]
            } for area_name, data in compliance_results.items() if data["status"] != "Compliant"]
            
            # Prepare visualization data
            visualization_data = {
                "areas": []
            }
            
            # Add score distribution data for visualization
            if compliance_results:
                for area_name, data in compliance_results.items():
                    visualization_data["areas"].append({
                        "name": area_name,
                        "status": data["status"],
                        "relevance": data["relevance"],
                        "relevance_score": data["relevance_score"],
                        "color": data["color"],
                        "risk_level": data["risk_level"],
                        "requirements": {
                            "total": len(data["requirements_met"]) + len(data["requirements_missing"]),
                            "met": len(data["requirements_met"]),
                            "missing": len(data["requirements_missing"])
                        }
                    })
            
            # Calculate overall compliance score
            if not compliance_results:
                overall_status = "Not Applicable"
                compliance_score = 100
            else:
                compliant_count = sum(1 for data in compliance_results.values() if data["status"] == "Compliant")
                partial_count = sum(1 for data in compliance_results.values() if data["status"] == "Partially Compliant")
                total_areas = len(compliance_results)
                
                compliance_score = (compliant_count * 100 + partial_count * 50) / total_areas
                
                if compliance_score >= 90:
                    overall_status = "Highly Compliant"
                elif compliance_score >= 70:
                    overall_status = "Mostly Compliant"
                elif compliance_score >= 40:
                    overall_status = "Partially Compliant"
                else:
                    overall_status = "Significant Issues"
            
            return {
                "overall_status": overall_status,
                "areas": areas_with_issues,
                "warnings": overall_issues,
                "compliant_areas": compliant_areas,
                "visualization": {
                    "areas": visualization_data["areas"],
                    "compliance_score": round(compliance_score, 1)
                },
                "detailed_results": compliance_results,
                "document_type": doc_type_info,
                "key_clauses": key_clauses
            }
            
        except Exception as e:
            print(f"Error in compliance check: {str(e)}")
            return {
                "overall_status": "Error",
                "areas": [],
                "warnings": [{
                    "message": f"Error analyzing compliance: {str(e)}", 
                    "level": "high"
                }],
                "compliant_areas": [],
                "visualization": {
                    "areas": [],
                    "compliance_score": 0
                }
            }

    def display_compliance_check(self, compliance_data: Dict[str, Any], output_format: str = 'text') -> Union[str, Dict[str, Any]]:
        """
        Displays compliance check results in a user-friendly format.
        
        Args:
            compliance_data: The result data from _check_compliance method
            output_format: 'text' for console-friendly text output or 'html' for web display
            
        Returns:
            Formatted compliance check results in the specified format (string for text, dict for HTML/JSON)
        """
        try:
            if output_format.lower() not in ['text', 'html', 'json']:
                raise ValueError(f"Unsupported output format: {output_format}")
                
            # Basic information to display
            overall_status = compliance_data.get('overall_status', 'Unknown')
            compliance_score = compliance_data.get('visualization', {}).get('compliance_score', 0)
            
            if output_format.lower() == 'text':
                # Create text-based output with ANSI color codes
                output = []
                
                # Define color codes
                colors = {
                    'green': '\033[92m',
                    'yellow': '\033[93m',
                    'red': '\033[91m',
                    'blue': '\033[94m',
                    'end': '\033[0m',
                    'bold': '\033[1m',
                    'underline': '\033[4m'
                }
                
                # Header
                output.append(f"{colors['bold']}COMPLIANCE CHECK RESULTS{colors['end']}")
                output.append("-" * 60)
                
                # Overall status with appropriate color
                status_color = 'green' if 'high' in overall_status.lower() else 'yellow' if 'mostly' in overall_status.lower() else 'red'
                output.append(f"Overall Status: {colors[status_color]}{overall_status}{colors['end']}")
                
                # Compliance score with color based on value
                score_color = 'green' if compliance_score >= 80 else 'yellow' if compliance_score >= 50 else 'red'
                output.append(f"Compliance Score: {colors[score_color]}{compliance_score}%{colors['end']}")
                output.append("")
                
                # Areas with issues
                if 'areas' in compliance_data and compliance_data['areas']:
                    output.append(f"{colors['bold']}AREAS WITH COMPLIANCE ISSUES{colors['end']}")
                    for i, area in enumerate(compliance_data['areas']):
                        area_color = 'yellow' if area['status'] == 'Partial' else 'red'
                        output.append(f"{i+1}. {colors[area_color]}{area['name']}{colors['end']} - {area['status']}")
                        output.append(f"   Relevance: {area['relevance']}")
                        output.append(f"   Risk Level: {area['risk_level']}")
                        
                        if 'requirements_met' in area and area['requirements_met']:
                            output.append(f"   {colors['green']}Requirements Met:{colors['end']}")
                            for req in area['requirements_met'][:3]:  # Show first 3
                                output.append(f"   ✓ {req}")
                        
                        if 'requirements_missing' in area and area['requirements_missing']:
                            output.append(f"   {colors['red']}Requirements Missing:{colors['end']}")
                            for req in area['requirements_missing'][:3]:  # Show first 3
                                output.append(f"   ✗ {req}")
                        output.append("")
                
                # Compliant areas
                if 'compliant_areas' in compliance_data and compliance_data['compliant_areas']:
                    output.append(f"{colors['bold']}COMPLIANT AREAS{colors['end']}")
                    for i, area in enumerate(compliance_data['compliant_areas']):
                        output.append(f"{i+1}. {colors['green']}{area}{colors['end']}")
                    output.append("")
                
                # Warnings
                if 'warnings' in compliance_data and compliance_data['warnings']:
                    output.append(f"{colors['bold']}WARNINGS{colors['end']}")
                    for i, warning in enumerate(compliance_data['warnings']):
                        severity = warning.get('level', 'Medium')
                        warning_color = 'red' if severity == 'High' else 'yellow' if severity == 'Medium' else 'blue'
                        output.append(f"{i+1}. {colors[warning_color]}{warning['message']}{colors['end']}")
                        if 'level' in warning:
                            output.append(f"   Severity: {severity}")
                    output.append("")
                
                # Recommendations
                if 'recommendations' in compliance_data and compliance_data['recommendations']:
                    output.append(f"{colors['bold']}RECOMMENDATIONS{colors['end']}")
                    for i, rec in enumerate(compliance_data['recommendations']):
                        output.append(f"{i+1}. {rec}")
                        
                return "\n".join(output)
                
            elif output_format.lower() == 'html' or output_format.lower() == 'json':
                # Create an HTML representation for web display
                # This structure will be easier to style with CSS in a web application
                html_structure = {
                    'title': 'Document Compliance Analysis',
                    'overall_status': {
                        'status': compliance_data.get('overall_status', 'Not Analyzed'),
                        'score': compliance_data.get('visualization', {}).get('compliance_score', 0)
                    },
                    'areas_with_issues': [],
                    'compliant_areas': [],
                    'warnings': [],
                    'recommendations': compliance_data.get('recommendations', []),
                    'visualization_data': compliance_data.get('visualization', {})
                }
                
                # Add document type information if available
                if 'document_type' in compliance_data and compliance_data['document_type']:
                    html_structure['document_type'] = {
                        'type': compliance_data['document_type'].get('document_type', 'Unknown'),
                        'sub_type': compliance_data['document_type'].get('sub_type'),
                        'confidence': compliance_data['document_type'].get('confidence', 0),
                        'indicators': compliance_data['document_type'].get('indicators', [])
                    }
                
                # Add key clauses if available
                if 'key_clauses' in compliance_data and compliance_data['key_clauses']:
                    html_structure['key_clauses'] = []
                    for clause in compliance_data['key_clauses'][:5]:  # Include top 5 key clauses
                        html_structure['key_clauses'].append({
                            'type': clause.get('clause_type', 'General'),
                            'content': clause.get('content', ''),
                            'importance': clause.get('importance', 0),
                            'risk_score': clause.get('risk_score', 0)
                        })
                
                # Process areas with issues
                if 'areas_with_issues' in compliance_data and compliance_data['areas_with_issues']:
                    for area in compliance_data['areas_with_issues']:
                        area_html = {
                            'name': area['name'],
                            'status': area['status'],
                            'relevance': area.get('relevance', 'Medium'),
                            'risk_level': area.get('risk_level', 'medium'),
                            'requirements_met': area.get('requirements_met', []),
                            'requirements_missing': area.get('requirements_missing', [])
                        }
                        html_structure['areas_with_issues'].append(area_html)
                
                # Process compliant areas
                if 'compliant_areas' in compliance_data and compliance_data['compliant_areas']:
                    for area in compliance_data['compliant_areas']:
                        if isinstance(area, dict):
                            html_structure['compliant_areas'].append(area)
                        else:
                            html_structure['compliant_areas'].append({'name': area})
                
                # Process warnings
                if 'warnings' in compliance_data and compliance_data['warnings']:
                    html_structure['warnings'] = compliance_data['warnings']
                    
                return html_structure
                
            else:  # JSON format
                # Return a clean, serializable version of the compliance data
                return compliance_data
                
        except Exception as e:
            print(f"Error displaying compliance check: {str(e)}")
            if output_format.lower() == 'text':
                return f"Error displaying compliance check: {str(e)}"
            else:
                return {'error': str(e)}

    def _extract_key_clauses(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key clauses from a legal document with importance and risk scores.
        
        Args:
            text: The document text to analyze
            
        Returns:
            List of dictionaries containing clause information including:
            - clause_type: Type of clause (e.g., "Limitation of Liability")
            - content: Text content of the clause
            - importance: Score indicating the importance of the clause (0-1)
            - risk_score: Score indicating the potential risk level (0-1)
        """
        if not text or len(text.strip()) < 100:
            return []
        
        # Split text into paragraphs for analysis
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        # Define patterns for different types of clauses with their risk weights
        clause_patterns = [
            {
                "type": "Limitation of Liability",
                "patterns": [
                    r'(?i)\b(limit(ation|ed)?\s+of\s+liability|limited\s+liability|no\s+liability|not\s+be\s+liable)\b',
                    r'(?i)\b(in\s+no\s+event\s+shall|shall\s+not\s+be\s+liable|disclaim\s+liability)\b',
                    r'(?i)\b(cap\s+on\s+liability|maximum\s+liability|aggregate\s+liability)\b'
                ],
                "importance": 0.9,
                "risk_weight": 0.8,
                "all_caps_boost": 0.1
            },
            {
                "type": "Indemnification",
                "patterns": [
                    r'(?i)\b(indemnif(y|ication|ies)|hold\s+harmless|defend)\b',
                    r'(?i)\b(indemnit(y|ies)|reimburse\s+.{0,30}\s+for\s+.{0,30}\s+loss(es)?)\b'
                ],
                "importance": 0.85,
                "risk_weight": 0.7,
                "all_caps_boost": 0.1
            },
            {
                "type": "Termination",
                "patterns": [
                    r'(?i)\b(terminat(e|ion|ing)|cancel(lation)?|expir(e|ation)|end\s+.{0,20}\s+agreement)\b',
                    r'(?i)\b(right\s+to\s+terminate|early\s+termination|notice\s+of\s+termination)\b'
                ],
                "importance": 0.8,
                "risk_weight": 0.6,
                "all_caps_boost": 0.05
            },
            {
                "type": "Intellectual Property",
                "patterns": [
                    r'(?i)\b(intellectual\s+property|ip|patent|copyright|trademark|trade\s+secret)\b',
                    r'(?i)\b(IP\s+rights|ownership\s+of|retain\s+ownership|assign\s+.{0,20}\s+right)\b'
                ],
                "importance": 0.8,
                "risk_weight": 0.6,
                "all_caps_boost": 0.05
            },
            {
                "type": "Confidentiality",
                "patterns": [
                    r'(?i)\b(confidential(ity)?|non[\-\s]?disclosure|trade\s+secret|proprietary\s+information)\b',
                    r'(?i)\b(disclos(e|ure)|maintain\s+.{0,20}\s+confiden(ce|tial))\b'
                ],
                "importance": 0.75,
                "risk_weight": 0.5,
                "all_caps_boost": 0.05
            },
            {
                "type": "Data Protection",
                "patterns": [
                    r'(?i)\b(data\s+protection|personal\s+data|data\s+privacy|gdpr|ccpa)\b',
                    r'(?i)\b(data\s+(processor|controller)|processing\s+of\s+data|data\s+subject)\b'
                ],
                "importance": 0.75,
                "risk_weight": 0.6,
                "all_caps_boost": 0.05
            },
            {
                "type": "Payment Terms",
                "patterns": [
                    r'(?i)\b(payment\s+terms|fee[s]?|compensation|invoice|billing)\b',
                    r'(?i)\b(price|cost|rate|amount|due\s+.{0,20}\s+pay(ment)?|late\s+fee)\b'
                ],
                "importance": 0.7,
                "risk_weight": 0.5,
                "all_caps_boost": 0.05
            },
            {
                "type": "Dispute Resolution",
                "patterns": [
                    r'(?i)\b(dispute\s+resolution|arbitration|mediation|jurisdiction)\b',
                    r'(?i)\b(governing\s+law|venue|forum|court|lawsuit|litigation)\b'
                ],
                "importance": 0.7,
                "risk_weight": 0.6,
                "all_caps_boost": 0.05
            },
            {
                "type": "Force Majeure",
                "patterns": [
                    r'(?i)\b(force\s+majeure|act\s+of\s+god|beyond\s+.{0,30}\s+control)\b',
                    r'(?i)\b(unforeseen\s+circumstances|disaster|pandemic|epidemic|emergency)\b'
                ],
                "importance": 0.6,
                "risk_weight": 0.4,
                "all_caps_boost": 0.05
            },
            {
                "type": "Warranty",
                "patterns": [
                    r'(?i)\b(warrant(y|ies)|guarantee|as\s+is|disclaims?\s+.{0,20}\s+warrant(y|ies))\b',
                    r'(?i)\b(no\s+warranty|without\s+warranty|disclaim\s+.{0,30}\s+warrant(y|ies))\b'
                ],
                "importance": 0.7,
                "risk_weight": 0.5,
                "all_caps_boost": 0.05
            },
            {
                "type": "Non-Compete",
                "patterns": [
                    r'(?i)\b(non[\-\s]?compete|restraint\s+of\s+trade|competitive\s+activity)\b',
                    r'(?i)\b(shall\s+not\s+.{0,30}\s+compet(e|itor)|during\s+.{0,20}\s+after)\b'
                ],
                "importance": 0.65,
                "risk_weight": 0.7,
                "all_caps_boost": 0.05
            },
            {
                "type": "Assignment",
                "patterns": [
                    r'(?i)\b(assign(ment)?|transfer\s+.{0,20}\s+(rights|obligations))\b',
                    r'(?i)\b(may\s+not\s+.{0,20}\s+assign|no\s+assignment|consent\s+to\s+assign)\b'
                ],
                "importance": 0.6,
                "risk_weight": 0.4,
                "all_caps_boost": 0.05
            },
            {
                "type": "Severability",
                "patterns": [
                    r'(?i)\b(sever(ability|able)|invalid\s+provision|unenforceable)\b',
                    r'(?i)\b(remaining\s+provisions|if\s+any\s+provision|provision\s+.{0,30}\s+invalid)\b'
                ],
                "importance": 0.5,
                "risk_weight": 0.2,
                "all_caps_boost": 0.05
            }
        ]
        
        extracted_clauses = []
        
        # Analyze each paragraph for clause matches
        for paragraph in paragraphs:
            if len(paragraph) < 20:  # Skip very short paragraphs
                continue
                
            # Check for section numbering patterns often found in legal documents
            section_pattern = r'^\s*(?:\d+(?:\.\d+)*|[a-zA-Z](?:\)|\.)|(\([a-z]\)|[IVXLCDM]+\.))?\s*'
            has_section_numbering = bool(re.match(section_pattern, paragraph))
            
            # Look for all caps text which often indicates importance
            all_caps_phrases = re.findall(r'\b[A-Z]{5,}\b', paragraph)
            has_all_caps = len(all_caps_phrases) > 0
            
            for clause_type in clause_patterns:
                for pattern in clause_type["patterns"]:
                    if re.search(pattern, paragraph):
                        # Calculate clause importance based on various factors
                        importance = clause_type["importance"]
                        
                        # Adjust importance based on text features
                        if has_section_numbering:
                            importance += 0.05
                        if has_all_caps:
                            importance += clause_type["all_caps_boost"]
                        
                        # Calculate risk score based on text features and patterns
                        risk_phrases = [
                            r'(?i)\b(shall\s+not|no\s+obligation|disclaim|waive|without\s+liability)\b.{0,50}\b(personal|data)\b',
                            r'(?i)\b(sole\s+discretion|exclusive\s+remedy|not\s+responsible|as\s+is)\b.{0,50}\b(liability|responsible|damages)\b',
                            r'(?i)\b(under\s+no\s+circumstances|not\s+.{0,20}\s+warrant|no\s+.{0,20}\s+warranty)\b.{0,50}\b(liability|responsible|damages)\b'
                        ]
                        
                        risk_score = clause_type["risk_weight"]
                        risk_indicators_count = sum(1 for p in risk_phrases if re.search(p, paragraph))
                        if risk_indicators_count > 0:
                            risk_score += 0.1 * min(risk_indicators_count, 3)  # Cap at +0.3
                        
                        # Cap final scores
                        importance = min(0.95, importance)
                        risk_score = min(0.95, risk_score)
                        
                        # Check for duplicates before adding
                        is_duplicate = False
                        for existing_clause in extracted_clauses:
                            if existing_clause["clause_type"] == clause_type["type"] and \
                               existing_clause["content"][:100] == paragraph[:100]:
                                is_duplicate = True
                                # Keep the higher importance one
                                if importance > existing_clause["importance"]:
                                    existing_clause["importance"] = importance
                                    existing_clause["risk_score"] = risk_score
                                break
                        
                        if not is_duplicate:
                            extracted_clauses.append({
                                "clause_type": clause_type["type"],
                                "content": paragraph,
                                "importance": round(importance, 2),
                                "risk_score": round(risk_score, 2)
                            })
                        break  # Stop checking other patterns for this clause type
        
        # Sort clauses by importance (descending)
        sorted_clauses = sorted(extracted_clauses, key=lambda x: x["importance"], reverse=True)
        
        # Return top clauses (up to 10)
        return sorted_clauses[:10]

    def _extract_topic_keywords(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract key topics from the document with relevant keywords.
        
        Args:
            text: Document text to analyze.
            
        Returns:
            List of topics with associated keywords and relevance scores.
        """
        try:
            if not text or len(text.strip()) < 100:
                return []
            
            # Clean and normalize text
            cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Extract topic keywords based on TF-IDF
            # This is a simplified implementation for illustration
            topics = [
                {
                    "topic": "Legal",
                    "keywords": ["agreement", "contract", "terms", "parties", "law"],
                    "score": 0.85
                },
                {
                    "topic": "Finance",
                    "keywords": ["payment", "fee", "cost", "price", "invoice"],
                    "score": 0.75
                },
                {
                    "topic": "Technology",
                    "keywords": ["software", "data", "system", "application", "device"],
                    "score": 0.65
                },
                {
                    "topic": "Privacy",
                    "keywords": ["personal", "information", "data", "protection", "gdpr"],
                    "score": 0.55
                },
                {
                    "topic": "Business",
                    "keywords": ["service", "product", "company", "business", "customer"],
                    "score": 0.45
                }
            ]
            
            # Filter topics based on keyword presence in the text
            relevant_topics = []
            for topic in topics:
                keyword_matches = [keyword for keyword in topic["keywords"] if keyword in cleaned_text]
                if keyword_matches:
                    # Calculate relevance based on matched keywords
                    relevance = min(1.0, len(keyword_matches) / len(topic["keywords"]) * topic["score"])
                    topic_copy = topic.copy()
                    topic_copy["score"] = relevance
                    relevant_topics.append(topic_copy)
            
            # Sort by relevance and round scores
            relevant_topics = sorted(relevant_topics, key=lambda x: x["score"], reverse=True)[:5]  # Top 5 topics
            
            # Round scores for cleaner display
            for topic in relevant_topics:
                topic["score"] = round(topic["score"], 1)
            
            return relevant_topics
        
        except Exception as e:
            print(f"Error in topic extraction: {str(e)}")
            return []
    
    def _extract_term_context(self, text: str, start_pos: int, end_pos: int, context_chars: int = 100) -> str:
        """
        Extract context around a legal term in text.
        
        Args:
            text: The full text containing the term
            start_pos: Start position of the term
            end_pos: End position of the term
            context_chars: Number of characters of context to extract on each side
            
        Returns:
            String with the term and its surrounding context
        """
        try:
            text_length = len(text)
            
            # Determine the context start and end positions
            context_start = max(0, start_pos - context_chars)
            context_end = min(text_length, end_pos + context_chars)
            
            # Extract the context
            prefix = "..." if context_start > 0 else ""
            suffix = "..." if context_end < text_length else ""
            
            # Extract the context
            context = prefix + text[context_start:context_end] + suffix
            
            return context
        except Exception as e:
            print(f"Error extracting term context: {str(e)}")
            return text[max(0, start_pos-10):min(len(text), end_pos+10)]
    
    def _format_pdf_date(self, date_string: str) -> str:
        """
        Format PDF date string (format D:YYYYMMDDHHmmSSOHH'mm') to a readable date format.
        
        Args:
            date_string: PDF date string in format D:YYYYMMDDHHmmSSOHH'mm'
            
        Returns:
            Formatted date string in YYYY-MM-DD HH:MM:SS format
        """
        return DocumentProcessor.format_pdf_date(date_string)
    
    async def _process_page(self, page):
        """
        Process a single page from a PDF document.
        
        Args:
            page: A PyMuPDF page object
        
        Returns:
            Dict with page content, tables, images, and other extracted information
        """
        return await DocumentProcessor.process_page(page)

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text using spaCy.
        
        Args:
            text: The text to extract entities from
            
        Returns:
            List of dictionaries containing entity text, label, start position, and end position
        """
        entities = []
        
        try:
            if self.nlp is None:
                return entities
                
            # Process text with spaCy
            doc = self.nlp(text[:1000000])  # Limit to prevent memory issues
            
            # Extract entities
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "context": self._extract_term_context(text, ent.start_char, ent.end_char)
                })
                
        except Exception as e:
            print(f"Error extracting entities: {str(e)}")
            
        return entities