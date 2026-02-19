import os
import requests
from google import genai
from typing import Type, List, Dict, Any
from urllib.parse import quote_plus
from crewai.tools import BaseTool
from trafilatura import fetch_url, extract
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class GoogleSearchToolInput(BaseModel):
    """Input schema for GoogleSearchTool."""
    query: str = Field(..., description="The search query to look up on Google.")
    num_results: int = Field(default=10, description="Number of search results to return (default: 10)")

class GoogleSearchTool(BaseTool):
    name: str = "GoogleSearchTool"
    description: str = "Performs a Google search using Custom Search API and returns relevant results including titles, descriptions, and URLs."
    args_schema: Type[BaseModel] = GoogleSearchToolInput
    api_key: str
    cx: str
    
    def __init__(self, api_key: str, cx: str):
        super().__init__(api_key=api_key, cx=cx)
        self.api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.cx = os.getenv("SEARCH_ENGINE_ID")

    def _summarize_text(self, text: str) -> str:
        """
        Sends a long text to the Gemini API for summarization using an optimized prompt.

        Args:
            text: The long input text (e.g., scraped article content) to be summarized.
            api_key: Your Google API key for accessing the Gemini API.
            target_length: Desired length of the summary. Options: "very short", "short", "concise", "detailed".
            summary_format: Desired format of the summary. Options: "paragraph", "bullet points".

        Returns:
            A string containing the generated summary, or an error message.
        """
        # Configure the generative AI model
        client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

        model = 'gemini-2.0-flash-lite'



        # Optimized Prompt
        # This prompt is designed to be clear, specific, and provides options for customization.
        prompt = f"""
        You are an expert summarization AI. Your goal is to provide a pithy and concise summary of the following text.

        Input Text:
        '''
        {text}
        '''

        Instructions:
        - Summarize the provided text accurately and objectively.
        - Focus on the main points and key information.
        - The summary should be complete but concise and contain all the information from the original text verbatim.
        - Format in 3-4 paragraphs.
        - Do not include any introductory or concluding phrases like "Here is a summary:" or "In conclusion,".
        - Ensure the summary is easy to understand and captures the essence plus critical details of the original text.
        - Add a prefix in parenthesis to the summary to indicate that it is a summary of the original text.
        """

        try:
            # Generate the content using the model
            response = client.models.generate_content(model=model, contents=prompt)

            # Return the summarized text
            return response.text

        except Exception as e:
            return f"An error occurred: {e}"


    def _run(self, query: str, num_results: int = 10) -> str:
        try:
            search_results = self._perform_search(query, num_results)
            processed_results = []
            for result in search_results:
                print(f"Processing result: {result['link']}")
                try:
                    text = self._get_article_text(result['link'])
                    if not text or len(text) < 150:
                        continue  # Skip this result
                    if len(text) > 3000:
                        text = self._summarize_text(text)
                    result['text'] = text
                    processed_results.append(result)
                except Exception as e:
                    print(f"Error getting text for {result['link']}: {e}")
                    result['text'] = ""
            formatted_results = "\n\n".join([
                f"Title: {result['title']}\nURL: {result['link']}\nText: {result['text']}"
                for result in processed_results
            ])
            return formatted_results
        except Exception as e:
            return f"Error performing search: {str(e)}"

    def _perform_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        url = f"https://www.googleapis.com/customsearch/v1?key={self.api_key}&cx={self.cx}&q={quote_plus(query)}&num={min(num_results, 10)}"
        
        response = requests.get(url)
        response.raise_for_status()
        results = response.json()
        
        if "items" not in results:
            return []
            
        return results["items"][:num_results]
    
    def _get_article_text(self, url):
        try:
            downloaded = fetch_url(url)
            return extract(downloaded)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return ""

if __name__ == "__main__":
    # Replace these with your actual API credentials
    api_key = os.getenv("GOOGLE_API_KEY")
    cx = os.getenv("SEARCH_ENGINE_ID")
    
    # Create an instance of the search tool
    search_tool = GoogleSearchTool(api_key=api_key, cx=cx)
    
    # Test search query
    test_query = "the Snooker World Championships 2025"
    
    # Execute the search
    results = search_tool._run(
        query=test_query,
        num_results=5
    )
    
    # Print the results
    print(f"Search Results for: {test_query}\n")
    print(results) 