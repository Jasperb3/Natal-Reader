from typing import Type
from google import genai
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os

gemini_api_key = os.environ.get("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key, http_options={'api_version': 'v1alpha'})

MODEL = 'gemini-2.5-flash-preview-04-17'


class GeminiSearchToolInput(BaseModel):
    """Input schema for GeminiSearchTool."""

    query: str = Field(..., description="The query to search the web for.")


class GeminiSearchTool(BaseTool):
    name: str = "Gemini Search Tool"
    description: str = (
        "Use this tool to get Gemini-curated web search results for a given query. Provide a natural language query as a single string."
    )
    args_schema: Type[BaseModel] = GeminiSearchToolInput

    def _run(self, query: str) -> str:
        search_tool = {'google_search': {}}
        chat = client.chats.create(model=MODEL, config={'tools': [search_tool]})

        r = chat.send_message(query)

        return r.text
    

if __name__ == "__main__":
    query = "What are the latest Prewmier League results of today?"
    tool = GeminiSearchTool()
    print(tool.run(query))
