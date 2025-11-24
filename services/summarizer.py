"""
Gemini API integration for summarization via Vertex AI
"""
import os
import vertexai
from vertexai.generative_models import GenerativeModel


class SummarizerService:
    """Service for summarizing transcriptions using Gemini via Vertex AI"""
    
    def __init__(self, project_id: str, credentials_path: str):
        # Initialize Vertex AI with service account credentials
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        vertexai.init(project=project_id, location="us-central1")
        self.model = GenerativeModel("gemini-2.5-flash")
    
    def summarize(self, transcription: str) -> str:
        """
        Generate a structured summary of the transcription
        
        Args:
            transcription: The text to summarize
            
        Returns:
            Structured summary with key points
        """
        if not transcription or transcription.startswith("Error") or transcription == "No speech detected in audio.":
            return "No summary available."
        
        prompt = f"""
Please provide a concise, structured summary of the following audio transcription.
Format the summary with:
- Main Topic: [topic]
- Key Points: [bullet points of main ideas]
- Action Items: [any tasks or actions mentioned, if applicable]

Keep it brief and well-organized.

Transcription:
{transcription}
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def generate_title(self, transcription: str) -> str:
        """
        Generate a short title for the note
        
        Args:
            transcription: The text to generate title from
            
        Returns:
            A short title (max 50 characters)
        """
        if not transcription or transcription.startswith("Error"):
            return "Untitled Note"
        
        prompt = f"""
Generate a very short title (maximum 5-6 words) for this audio note.
Only return the title, nothing else.

Transcription:
{transcription[:500]}
"""
        
        try:
            response = self.model.generate_content(prompt)
            title = response.text.strip().replace('"', '').replace("'", "")
            return title[:50] if len(title) > 50 else title
        except Exception as e:
            return "Untitled Note"
