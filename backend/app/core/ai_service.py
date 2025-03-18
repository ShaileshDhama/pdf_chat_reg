import openai
from typing import Optional, List
from app.core.config import settings
from app.core.redis_manager import redis_manager

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY

    async def generate_response(self, 
                              message: str, 
                              user_id: str, 
                              context_window: int = 5) -> str:
        """Generate AI response using chat context"""
        # Get recent chat history
        chat_history = redis_manager.get_chat_history(user_id, context_window)
        
        # Build conversation context
        messages = [{"role": "system", "content": """You are a helpful AI assistant. 
                    Your responses should be informative, engaging, and natural.
                    You can help with document analysis, answer questions, and engage in conversation."""}]
        
        # Add chat history for context
        for hist_msg in reversed(chat_history):
            role = "user" if hist_msg["is_user"] else "assistant"
            messages.append({"role": role, "content": hist_msg["content"]})
        
        # Add current message
        messages.append({"role": "user", "content": message})

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."

    async def analyze_document(self, file_content: str, query: Optional[str] = None) -> str:
        """Analyze document content and generate insights"""
        prompt = f"""Analyze the following document content and provide insights.
                    If a specific query is provided, focus on answering that query.
                    Document content: {file_content[:4000]}  # Limit content length
                    Query: {query if query else 'Provide general insights and key points'}"""

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a document analysis expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800,
                top_p=1
            )
            
            return response.choices[0].message.content

        except Exception as e:
            print(f"Error analyzing document: {e}")
            return "I apologize, but I'm having trouble analyzing the document right now. Please try again."

ai_service = AIService()
