import os
from typing import Any, Optional, Type
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ConfigDict

load_dotenv()

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = Any  # type placeholder
    Filter = Any
    FieldCondition = Any
    MatchValue = Any

from crewai.tools import BaseTool


class QdrantSearchToolSchema(BaseModel):
    """Input for QdrantSearchTool."""

    query: str = Field(
        ...,
        description="The word or phrase to search for in the astrology reference docs. Must be a single string to match on similarity.",
    )
    # filter_by: Optional[str] = Field(
    #     default=None,
    #     description="Optional: The name of the metadata field to filter by (e.g., 'source').",
    # )
    # filter_value: Optional[str] = Field(
    #     default=None,
    #     description="Optional: The value to match for the filter_by field (e.g., 'AAPL_10-K.md').",
    # )


class QdrantSearchTool(BaseTool):
    """
    Custom tool to search a Qdrant database for relevant information,
    specifically designed for the 'stock_knowledge' collection.
    """
    model_config = {"arbitrary_types_allowed": True}
    client: QdrantClient = None
    name: str = "QdrantSearchTool"
    description: str = (
        "A tool to search astrology reference docs for relevant information"
    )
    args_schema: Type[BaseModel] = QdrantSearchToolSchema
    collection_name: str = Field(
        default=os.environ.get("QDRANT_COLLECTION_NAME"), description="Name of the Qdrant collection to search."
    )
    limit: int = Field(default=5, description="Maximum number of results to return.")
    score_threshold: float = Field(
        default=0.2, description="Minimum similarity score threshold."
    )
    qdrant_url: Optional[str] = Field(
        default=None, description="The URL of the Qdrant server."
    )
    qdrant_api_key: Optional[str] = Field(
        default=None, description="The API key for the Qdrant server."
    )
    custom_embedding_fn: Optional[callable] = Field(
        default=None,
        description="Optional custom embedding function. Defaults to Gemini embeddings.",
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.qdrant_url = os.environ.get("QDRANT_CLUSTER_URL")
        self.qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        self.collection_name = os.environ.get(
            "QDRANT_COLLECTION_NAME", "astro_knowledge"
        )  # Use env, fallback to default

        if not self.qdrant_url or not self.qdrant_api_key:
            raise ValueError(
                "QDRANT_CLUSTER_URL and QDRANT_API_KEY must be set as environment variables."
            )

        if QDRANT_AVAILABLE:
            self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        else:
            raise ImportError(
                "The 'qdrant-client' package is required.  Install it with: pip install qdrant-client"
            )

    def _run(
        self,
        query: str,
        # filter_by: Optional[str] = None,
        # filter_value: Optional[str] = None,
    ) -> str:
        """Execute vector similarity search on Qdrant."""

        if not self.client:
            return "Qdrant client not initialized."

        search_filter = None
        # if filter_by and filter_value:
        #     search_filter = Filter(
        #         must=[FieldCondition(key=filter_by, match=MatchValue(value=filter_value))]
        #     )

        try:
            if self.custom_embedding_fn:
                query_vector = self.custom_embedding_fn(query)
            else:
                # Use the custom Gemini embedding function from utils
                from natal_reader.utils.embeddings_fn import (
                    custom_gemini_embedding_fn,
                )

                query_vector = custom_gemini_embedding_fn(query)

            if query_vector is None:
                return "Error: Could not generate embedding for the query."

            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=self.limit,
                score_threshold=self.score_threshold,
            )

            results = []
            for point in search_results:
                results.append(
                    {
                        "metadata": point.payload.get("source", ""),
                        "context": point.payload.get("text", ""),
                        "score": point.score,
                    }
                )
            return str(results)

        except Exception as e:
            return f"Error during Qdrant search: {e}"


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    # Example usage with dummy environment variables
    os.environ["QDRANT_CLUSTER_URL"] = os.environ.get("QDRANT_CLUSTER_URL")  # your qdrant url
    os.environ["QDRANT_API_KEY"] = os.environ.get("QDRANT_API_KEY")  # your qdrant api key
    os.environ["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY") # your gemini api key

    if (
        not os.environ.get("QDRANT_CLUSTER_URL")
        or not os.environ.get("QDRANT_API_KEY")
        or not os.environ.get("GEMINI_API_KEY")
    ):
        print(
            "Please set QDRANT_CLUSTER_URL, QDRANT_API_KEY and GEMINI_API_KEY environment variables."
        )
        exit(1)

    tool = QdrantSearchTool()
    query = "What is the ruler of the 1st house?"
    result = tool._run(query=query)
    print(result) 