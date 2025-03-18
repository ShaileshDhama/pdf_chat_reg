from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.node_parser import SimpleNodeParser
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import easyocr
from deep_translator import GoogleTranslator
from backend.app.utils.logger import logger

class LegalProcessor:
    """Advanced AI-powered legal document processor"""
    
    def __init__(self):
        # Initialize AI models
        self.llm = ChatOpenAI(model_name="gpt-4")
        self.embeddings = OpenAIEmbeddings()
        self.ocr_reader = easyocr.Reader(['en'])  # Simplified to just English for now
        
        # Initialize llama-index components
        Settings.llm = self.llm
        Settings.embed_model = self.embeddings
        self.node_parser = SimpleNodeParser()

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a legal document and extract key information."""
        try:
            # Read document text
            text = await self._read_document(file_path)
            
            # Create document index
            documents = [Document(text=text)]
            index = VectorStoreIndex.from_documents(documents)
            
            # Extract key information
            analysis = {
                "summary": await self._generate_summary(text),
                "key_points": await self._extract_key_points(text),
                "entities": await self._extract_entities(text),
                "recommendations": await self._generate_recommendations(text)
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _read_document(self, file_path: str) -> str:
        """Read text from document, with OCR fallback."""
        try:
            # For now, just read as text
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading document: {str(e)}")
            return ""

    async def _generate_summary(self, text: str) -> str:
        """Generate a concise summary of the legal document."""
        prompt = PromptTemplate(
            input_variables=["text"],
            template="Summarize the following legal document in 3-4 sentences:\n\n{text}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(text=text[:4000])  # Limit text length
        return result.strip()

    async def _extract_key_points(self, text: str) -> List[str]:
        """Extract key legal points from the document."""
        prompt = PromptTemplate(
            input_variables=["text"],
            template="Extract 5 key legal points from this document:\n\n{text}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(text=text[:4000])
        return [point.strip() for point in result.split('\n') if point.strip()]

    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract important legal entities."""
        entities = {
            "parties": [],
            "dates": [],
            "monetary_values": [],
            "locations": []
        }
        # Add entity extraction logic here
        return entities

    async def _generate_recommendations(self, text: str) -> List[str]:
        """Generate legal recommendations based on document content."""
        prompt = PromptTemplate(
            input_variables=["text"],
            template="Provide 3 legal recommendations based on this document:\n\n{text}"
        )
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(text=text[:4000])
        return [rec.strip() for rec in result.split('\n') if rec.strip()]

    async def query_document(self, query: str, context: str) -> Dict[str, Any]:
        """Query the document with a specific question."""
        try:
            # Create document index
            documents = [Document(text=context)]
            index = VectorStoreIndex.from_documents(documents)
            
            # Query the index
            query_engine = index.as_query_engine()
            response = query_engine.query(query)
            
            return {
                "success": True,
                "answer": str(response),
                "sources": []  # Add source tracking if needed
            }
            
        except Exception as e:
            logger.error(f"Error querying document: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
