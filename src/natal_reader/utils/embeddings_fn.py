from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

def custom_gemini_embedding_fn(text):
    """Generate embeddings for text using Gemini API."""

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    genai_client = genai.Client(api_key=gemini_api_key)

    try:
        if not genai_client:
            print("❌ Gemini client not initialized. Cannot generate embeddings.")
            return None

        result = genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=text
        )
        # Extract the list of floats from the embeddings object
        if result and result.embeddings and result.embeddings[0].values :
          return result.embeddings[0].values
        else:
          print ("❌ Gemini embedding values are empty")
          return None

    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None