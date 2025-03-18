from typing import List, Dict, Any, Optional
from pathlib import Path
import spacy
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import os
import fitz  # PyMuPDF
import re
from datetime import datetime
import tempfile
import PyPDF2
import docx
import textblob

__all__ = ['DocumentAnalyzer']

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
try:
    nltk.data.find('chunkers/maxent_ne_chunker')
except LookupError:
    nltk.download('maxent_ne_chunker')
try:
    nltk.data.find('corpora/words')
except LookupError:
    nltk.download('words')
try:
    nltk.data.find('sentiment/vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')

class DocumentAnalyzer:
    """Document analysis class for processing and analyzing text documents."""
    
    def __init__(self):
        try:
            self.ner = spacy.load("en_core_web_sm")
        except Exception as e:
            print(f"Warning: Could not load spaCy model: {str(e)}")
            self.ner = None
            
        try:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
        except Exception as e:
            print(f"Warning: Could not initialize sentiment analyzer: {str(e)}")
            self.sentiment_analyzer = None

    def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and return its analysis."""
        try:
            # Extract text from document
            text = self._extract_text(file_path)
            
            # Perform analysis
            analysis = {
                "text": text[:1000],  # First 1000 chars as preview
                "summary": self._generate_summary(text),
                "entities": self._extract_entities(text),
                "sentiment": self._analyze_sentiment(text),
                "key_phrases": self._extract_key_phrases(text),
                "legal_analysis": self._analyze_legal_context(text),
                "metrics": self._calculate_metrics(text)
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_text(self, file_path: str) -> str:
        """Extract text from various document formats."""
        file_path = Path(file_path)
        
        if file_path.suffix.lower() == '.pdf':
            return self._read_pdf(file_path)
        elif file_path.suffix.lower() == '.docx':
            return self._read_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def _read_pdf(self, file_path: Path) -> str:
        """Read content from PDF file."""
        text = ""
        try:
            # Try PyMuPDF first
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text()
        except Exception as e1:
            try:
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text()
            except Exception as e2:
                raise Exception(f"Failed to read PDF: {str(e1)} and {str(e2)}")
        
        return text

    def _read_docx(self, file_path: Path) -> str:
        """Read content from DOCX file."""
        try:
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            raise Exception(f"Failed to read DOCX: {str(e)}")

    def _generate_summary(self, text: str) -> str:
        """Generate a simple summary of the text."""
        # Simple summary - first few sentences
        sentences = nltk.sent_tokenize(text)
        return " ".join(sentences[:3])

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities using spaCy."""
        if not self.ner:
            return []
        
        doc = self.ner(text[:10000])  # Limit text length for performance
        return [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER."""
        if not self.sentiment_analyzer:
            return {}
        
        scores = self.sentiment_analyzer.polarity_scores(text)
        sentiment = "neutral"
        if scores["compound"] >= 0.05:
            sentiment = "positive"
        elif scores["compound"] <= -0.05:
            sentiment = "negative"
            
        return {
            "label": sentiment,
            "scores": scores
        }

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases using NLTK."""
        words = nltk.word_tokenize(text)
        tagged = nltk.pos_tag(words)
        
        # Extract noun phrases
        grammar = "NP: {<DT>?<JJ>*<NN>}"
        cp = nltk.RegexpParser(grammar)
        result = cp.parse(tagged)
        
        phrases = []
        for subtree in result.subtrees(filter=lambda t: t.label() == 'NP'):
            phrase = ' '.join([word for word, tag in subtree.leaves()])
            if len(phrase.split()) > 1:  # Only phrases with multiple words
                phrases.append(phrase)
        
        return phrases[:10]  # Return top 10 phrases

    def _analyze_legal_context(self, text: str) -> Dict[str, Any]:
        """Basic legal context analysis."""
        legal_terms = [
            "agreement", "contract", "party", "parties", "shall", "terms",
            "conditions", "law", "legal", "rights", "obligations"
        ]
        
        found_terms = []
        for term in legal_terms:
            if re.search(r'\b' + term + r'\b', text.lower()):
                found_terms.append(term)
                
        return {
            "legal_terms_found": found_terms,
            "is_legal_document": len(found_terms) > 3
        }

    def _calculate_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate various text metrics."""
        words = nltk.word_tokenize(text)
        sentences = nltk.sent_tokenize(text)
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "average_sentence_length": len(words) / len(sentences) if sentences else 0
        }

    def query_document(self, query: str) -> Dict[str, Any]:
        """Basic document querying functionality."""
        return {
            "success": True,
            "answer": "This feature is not implemented yet.",
            "sources": []
        }
