import os
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
import aiofiles
import asyncio
from datetime import datetime
import hashlib
import json
import re
import time

from .document_parser import DocumentParser
from ..schemas import DocumentAnalysis, AnalysisResult

class DocumentService:
    def __init__(self):
        self.parser = DocumentParser()
        self.upload_dir = "uploads"
        self.cache_dir = "cache"
        self._ensure_directories()
        
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for directory in [self.upload_dir, self.cache_dir]:
            os.makedirs(directory, exist_ok=True)
    
    async def process_document(self, file: UploadFile) -> DocumentAnalysis:
        """
        Process an uploaded document and return analysis results.
        """
        try:
            # Save uploaded file
            file_path = await self._save_upload(file)
            
            # Check cache first
            cache_result = await self._check_cache(file_path)
            if cache_result:
                return DocumentAnalysis(**cache_result)
            
            # Perform analysis
            analysis_result = await self._analyze_document(file_path)
            
            # Cache results
            await self._cache_results(file_path, analysis_result)
            
            return DocumentAnalysis(**analysis_result)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")
    
    async def _save_upload(self, file: UploadFile) -> str:
        """
        Save uploaded file and return its path.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(self.upload_dir, filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        return file_path
    
    async def _check_cache(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Check if analysis results are cached for the file.
        """
        cache_key = self._generate_cache_key(file_path)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_path):
            try:
                async with aiofiles.open(cache_path, 'r') as cache_file:
                    content = await cache_file.read()
                    return json.loads(content)
            except:
                return None
        
        return None
    
    async def _cache_results(self, file_path: str, results: Dict[str, Any]):
        """
        Cache analysis results for future use.
        """
        cache_key = self._generate_cache_key(file_path)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        async with aiofiles.open(cache_path, 'w') as cache_file:
            await cache_file.write(json.dumps(results))
    
    def _generate_cache_key(self, file_path: str) -> str:
        """
        Generate a cache key based on file content.
        """
        with open(file_path, 'rb') as f:
            content = f.read()
            return hashlib.sha256(content).hexdigest()
    
    async def _analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis.
        """
        # Analyze document using parser
        analysis_result = await self.parser.analyze_document(file_path)
        
        # Extract key information
        result = {
            "file_info": {
                "name": os.path.basename(file_path),
                "size": os.path.getsize(file_path),
                "type": os.path.splitext(file_path)[1][1:],
                "created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                "modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            },
            "metadata": analysis_result["metadata"],
            "content": {
                "text": analysis_result["content"],
                "summary": analysis_result["summary"],
                "language": analysis_result["language"],
                "structure": analysis_result["structure"]
            },
            "analysis": {
                "entities": analysis_result["entities"],
                "topics": analysis_result["analysis"]["topics"],
                "key_phrases": analysis_result["analysis"]["key_phrases"],
                "sentiment": analysis_result["analysis"]["sentiment"],
                "readability": analysis_result["analysis"]["readability_score"]
            },
            "elements": {
                "tables": analysis_result["tables"],
                "images": analysis_result["images"]
            },
            "compliance": analysis_result["analysis"]["compliance"],
            "risks": analysis_result["analysis"]["risk_factors"]
        }
        
        return result
    
    async def compare_documents(self, doc1_path: str, doc2_path: str) -> Dict[str, Any]:
        """
        Compare two documents and identify similarities and differences.
        """
        # Analyze both documents
        doc1_analysis = await self.parser.analyze_document(doc1_path)
        doc2_analysis = await self.parser.analyze_document(doc2_path)
        
        # Compare content
        comparison = {
            "similarity_score": self._calculate_similarity(
                doc1_analysis["content"],
                doc2_analysis["content"]
            ),
            "common_entities": self._compare_entities(
                doc1_analysis["entities"],
                doc2_analysis["entities"]
            ),
            "structural_differences": self._compare_structure(
                doc1_analysis["structure"],
                doc2_analysis["structure"]
            ),
            "risk_comparison": self._compare_risks(
                doc1_analysis["analysis"]["risk_factors"],
                doc2_analysis["analysis"]["risk_factors"]
            )
        }
        
        return comparison
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate text similarity using spaCy.
        """
        doc1 = self.parser.nlp(text1)
        doc2 = self.parser.nlp(text2)
        
        return doc1.similarity(doc2)
    
    def _compare_entities(self, entities1: List[Dict], entities2: List[Dict]) -> Dict[str, Any]:
        """
        Compare named entities between documents.
        """
        entities1_set = {(e["text"], e["label"]) for e in entities1}
        entities2_set = {(e["text"], e["label"]) for e in entities2}
        
        return {
            "common": list(entities1_set & entities2_set),
            "unique_to_first": list(entities1_set - entities2_set),
            "unique_to_second": list(entities2_set - entities1_set)
        }
    
    def _compare_structure(self, structure1: List[Dict], structure2: List[Dict]) -> Dict[str, Any]:
        """
        Compare document structures.
        """
        sections1 = [(s["heading"], s["type"]) for s in structure1]
        sections2 = [(s["heading"], s["type"]) for s in structure2]
        
        return {
            "matching_sections": list(set(sections1) & set(sections2)),
            "different_sections": {
                "first_only": list(set(sections1) - set(sections2)),
                "second_only": list(set(sections2) - set(sections1))
            }
        }
    
    def _compare_risks(self, risks1: List[Dict], risks2: List[Dict]) -> Dict[str, Any]:
        """
        Compare risk factors between documents.
        """
        def risk_key(risk):
            return f"{risk['severity']}:{risk['text']}"
        
        risks1_set = {risk_key(r) for r in risks1}
        risks2_set = {risk_key(r) for r in risks2}
        
        return {
            "common_risks": list(risks1_set & risks2_set),
            "unique_to_first": list(risks1_set - risks2_set),
            "unique_to_second": list(risks2_set - risks1_set)
        }
    
    async def extract_clauses(self, file_path: str, clause_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract specific types of clauses from the document.
        """
        analysis_result = await self.parser.analyze_document(file_path)
        
        # Define clause patterns based on common legal document structures
        clause_patterns = {
            "definition": r"(?i)(['']|means|shall mean|is defined as)",
            "obligation": r"(?i)(shall|must|will|agrees to|is required to)",
            "prohibition": r"(?i)(shall not|must not|may not|is prohibited|will not)",
            "termination": r"(?i)(terminat(e|ion)|cancel(led)?|end(ed)?)",
            "warranty": r"(?i)(warrant(s|y|ies)|represent(s|ation)|guarantee(s)?)",
            "liability": r"(?i)(liab(le|ility)|indemnif(y|ication)|damage(s)?)",
            "confidentiality": r"(?i)(confidential|secret|proprietary|non-disclosure)",
            "payment": r"(?i)(pay(ment)?|fee(s)?|cost(s)?|price|compensation)",
            "governing_law": r"(?i)(govern(ing)?.*law|jurisdiction|applicable.*law)"
        }
        
        import re
        clauses = []
        
        # Process each section
        for section in analysis_result["structure"]:
            text = section["content"]
            
            # If specific clause types are requested, only look for those
            patterns_to_check = {
                k: v for k, v in clause_patterns.items()
                if not clause_types or k in clause_types
            }
            
            # Check each pattern
            for clause_type, pattern in patterns_to_check.items():
                matches = re.finditer(pattern, text, re.MULTILINE)
                
                for match in matches:
                    # Get the sentence containing the clause
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end]
                    
                    clauses.append({
                        "type": clause_type,
                        "text": match.group(),
                        "context": context,
                        "section": section["heading"],
                        "position": {
                            "start": match.start(),
                            "end": match.end()
                        }
                    })
        
        return clauses
    
    async def analyze_clauses(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze extracted clauses for risks and implications.
        """
        analysis = {
            "by_type": {},
            "risk_assessment": [],
            "recommendations": []
        }
        
        # Group clauses by type
        for clause in clauses:
            clause_type = clause["type"]
            if clause_type not in analysis["by_type"]:
                analysis["by_type"][clause_type] = []
            analysis["by_type"][clause_type].append(clause)
        
        # Analyze each clause type
        for clause_type, type_clauses in analysis["by_type"].items():
            # Assess risks based on clause type
            risks = self._assess_clause_risks(clause_type, type_clauses)
            analysis["risk_assessment"].extend(risks)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(clause_type, risks)
            analysis["recommendations"].extend(recommendations)
        
        return analysis
    
    def _assess_clause_risks(self, clause_type: str, clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Assess risks for specific types of clauses.
        """
        risks = []
        
        # Risk assessment logic based on clause type
        risk_patterns = {
            "obligation": {
                "high": r"(?i)(immediate|strict|absolute|unconditional)",
                "medium": r"(?i)(reasonable|commercially reasonable|best efforts)",
                "low": r"(?i)(may|option|discretion)"
            },
            "liability": {
                "high": r"(?i)(unlimited|any and all|consequential)",
                "medium": r"(?i)(limited to|cap|threshold)",
                "low": r"(?i)(exclude|not liable|no responsibility)"
            },
            # Add patterns for other clause types
        }
        
        if clause_type in risk_patterns:
            import re
            patterns = risk_patterns[clause_type]
            
            for clause in clauses:
                for severity, pattern in patterns.items():
                    if re.search(pattern, clause["text"]):
                        risks.append({
                            "clause_type": clause_type,
                            "severity": severity,
                            "text": clause["text"],
                            "reason": f"Contains {severity} risk language: {pattern}"
                        })
        
        return risks
    
    def _generate_recommendations(self, clause_type: str, risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on identified risks.
        """
        recommendations = []
        
        # Recommendation templates based on clause type and risk severity
        templates = {
            "obligation": {
                "high": "Consider adding flexibility to the obligation with terms like 'commercially reasonable efforts'",
                "medium": "Review the reasonableness standard and consider if it needs more specificity",
                "low": "Consider if more specific obligations would better protect your interests"
            },
            "liability": {
                "high": "Consider adding liability caps or excluding certain types of damages",
                "medium": "Review liability caps to ensure they are appropriate for the risk",
                "low": "Consider if the liability exclusions are too broad"
            },
            # Add templates for other clause types
        }
        
        # Generate recommendations based on identified risks
        for risk in risks:
            if risk["clause_type"] in templates and risk["severity"] in templates[risk["clause_type"]]:
                recommendations.append({
                    "clause_type": risk["clause_type"],
                    "severity": risk["severity"],
                    "recommendation": templates[risk["clause_type"]][risk["severity"]]
                })
        
        return recommendations

    def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about a document file.
        """
        try:
            # Get file information
            file_info = {
                "name": os.path.basename(file_path),
                "size": os.path.getsize(file_path),
                "file_type": os.path.splitext(file_path)[1][1:].upper(),
                "last_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            }
            
            # Get page count based on file extension
            extension = os.path.splitext(file_path)[1].lower()
            page_count = 1  # Default for text files
            
            if extension in [".pdf"]:
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(file_path)
                    page_count = doc.page_count
                    doc.close()
                except Exception as e:
                    print(f"Error getting PDF page count: {str(e)}")
            
            file_info["page_count"] = page_count
            file_info["metadata"] = {}
            
            return file_info
        except Exception as e:
            # Log the error and return basic info
            print(f"Error getting document info: {str(e)}")
            return {
                "name": os.path.basename(file_path),
                "size": os.path.getsize(file_path),
                "file_type": os.path.splitext(file_path)[1][1:].upper(),
                "page_count": 1
            }
    
    def analyze_document(self, file_path: str, analysis_type: str = "basic", extract_entities: bool = True, perform_ocr: bool = True) -> Dict[str, Any]:
        """
        Public method to analyze a document with enhanced results and error handling.
        """
        try:
            # Get basic document info
            analysis_start = time.time()
            doc_info = self.get_document_info(file_path)
            
            # Create a new event loop for this method
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create a new event loop if one doesn't exist in this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async analysis with proper error handling
            try:
                analysis_result = loop.run_until_complete(self.parser.analyze_document(file_path))
            except Exception as e:
                print(f"Error in document parser: {str(e)}")
                # Create a fallback analysis result with minimal information
                analysis_result = {
                    "content": f"Failed to analyze content: {str(e)}",
                    "language": "en",
                    "entities": [],
                    "summary": "Analysis failed due to parsing error. Please check the document format.",
                    "structure": [],
                    "analysis": {
                        "document_type": "unknown",
                        "readability_score": 0,
                        "key_phrases": [],
                        "sentiment": {"score": 0, "label": "neutral", "confidence": 0},
                        "topics": [],
                        "legal_terms": [],
                        "references": [],
                        "risk_factors": [],
                        "compliance": {}
                    }
                }
            
            # Calculate analysis duration
            analysis_duration = time.time() - analysis_start
            
            # Determine word count intelligently
            word_count = 0
            if "content" in analysis_result and analysis_result["content"]:
                content = analysis_result["content"]
                # More accurate word count - filter out non-word elements
                words = re.findall(r'\b[^\W\d_]+\b', content)
                word_count = len(words)
            
            # Structure the result in the new format expected by the app
            result = {
                "file_info": {
                    "name": doc_info["name"],
                    "type": doc_info["file_type"],
                    "size": doc_info["size"],
                    "page_count": doc_info["page_count"],
                    "language": analysis_result.get("language", "en"),
                    "analyzed_at": datetime.now().isoformat(),
                    "analysis_duration_ms": round(analysis_duration * 1000),
                    "document_type": analysis_result.get("analysis", {}).get("document_type", "unknown")
                },
                "content": {
                    "text": analysis_result.get("content", ""),
                    "summary": analysis_result.get("summary", "No summary available."),
                    "structure": analysis_result.get("structure", [])
                },
                "analysis": {
                    "readability_score": analysis_result.get("analysis", {}).get("readability_score", 0),
                    "sentiment": analysis_result.get("analysis", {}).get("sentiment", {"score": 0, "label": "neutral"}),
                    "legal_terms": analysis_result.get("analysis", {}).get("legal_terms", []),
                    "key_phrases": analysis_result.get("analysis", {}).get("key_phrases", []),
                    "topics": analysis_result.get("analysis", {}).get("topics", []),
                    "risk_factors": analysis_result.get("analysis", {}).get("risk_factors", []),
                    "references": analysis_result.get("analysis", {}).get("references", [])
                },
                "entities": analysis_result.get("entities", []),
                "tables": analysis_result.get("tables", []),
                "images": analysis_result.get("images", [])
            }
            
            return result
            
        except Exception as e:
            print(f"Error in analyze_document: {str(e)}")
            # Return basic structure with error information
            return {
                "file_info": {
                    "name": os.path.basename(file_path),
                    "type": os.path.splitext(file_path)[1][1:].upper(),
                    "size": os.path.getsize(file_path),
                    "page_count": 1,
                    "error": str(e)
                },
                "content": {
                    "text": "",
                    "summary": "Analysis failed due to an error."
                },
                "analysis": {
                    "readability_score": 0,
                    "sentiment": {"score": 0, "label": "neutral"},
                    "legal_terms": [],
                    "key_phrases": [],
                    "topics": [],
                    "risk_factors": [],
                    "references": []
                },
                "entities": [],
                "tables": [],
                "images": []
            }
    
    def _calculate_avg_sentence_length(self, text: str) -> float:
        """
        Calculate the average sentence length in words.
        """
        if not text:
            return 0
            
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0
            
        total_words = sum(len(re.findall(r'\b[^\W\d_]+\b', sentence)) for sentence in sentences)
        return round(total_words / len(sentences), 1)
