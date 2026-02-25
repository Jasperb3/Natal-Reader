import os
import uuid
from pathlib import Path
from google import genai
from qdrant_client import QdrantClient
from qdrant_client.models import (
    PointStruct,
    Distance,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from natal_reader.utils.constants import DOCS_DIR
import time


class Setup:
    def __init__(self, state):
        self.state = state
        # Initialize Gemini client
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if self.gemini_api_key:
            # genai.configure(api_key=self.gemini_api_key)
            self.genai_client = genai.Client(api_key=self.gemini_api_key)
        else:
            print("⚠️ GEMINI_API_KEY not found in environment variables")
            self.genai_client = None

        # Initialize Qdrant client
        self.qdrant_url = os.environ.get("QDRANT_CLUSTER_URL")
        self.qdrant_api_key = os.environ.get("QDRANT_API_KEY")
        if self.qdrant_url and self.qdrant_api_key:
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url, api_key=self.qdrant_api_key
            )
        else:
            print("⚠️ QDRANT_URL or QDRANT_API_KEY not found in environment variables")
            self.qdrant_client = None

        # Collection name for Qdrant
        self.collection_name = os.environ.get("QDRANT_COLLECTION_NAME")

        # Initialize QdrantVectorSearchTool to None (will be set up later if Qdrant setup is successful)
        self.qdrant_tool = None

        # Keep track of processed files to avoid duplicates
        self.processed_files = set()

    def process_new_markdown_files(self):
        """Find and process new markdown files in the astro_docs directory."""
        print("Checking for new markdown files...")

        md_files = list(DOCS_DIR.glob("*.md"))

        # Check which files are actually new by checking if they exist in Qdrant
        new_files = []
        for md_file in md_files:
            # Skip files we've already processed in this session
            if str(md_file) in self.processed_files:
                continue

            # Check if this file already exists in Qdrant
            if self.qdrant_client and self.qdrant_client.collection_exists(
                self.collection_name
            ):
                source_name = md_file.name
                try:
                    count_result = self.qdrant_client.count(
                        collection_name=self.collection_name,
                        count_filter=Filter(
                            must=[
                                FieldCondition(
                                    key="source",
                                    match=MatchValue(value=source_name),
                                )
                            ]
                        ),
                    )

                    if count_result.count > 0:
                        # File already exists in Qdrant, mark as processed
                        print(
                            f"File {source_name} already exists in Qdrant with {count_result.count} chunks"
                        )
                        self.processed_files.add(str(md_file))
                        continue
                except Exception as e:
                    print(f"Error checking if {source_name} exists in Qdrant: {e}")

            # If we got here, the file is new and needs processing
            new_files.append(md_file)

        if not new_files:
            print("No new markdown files found.")
            return 0

        print(f"Found {len(new_files)} new markdown files to process.")

        for file_path in new_files:
            try:
                # Extract text from the file
                file_path_obj, text_chunks = self.extract_text_from_markdown(
                    [file_path]
                )  # Pass as a list
                if not text_chunks:
                    print(f"⚠️ No text chunks extracted from {file_path}")
                    continue

                print(
                    f"Extracted {len(text_chunks)} chunks from {file_path_obj}"
                )  # Log filename early

                # Generate embeddings
                embeddings_with_text = self.generate_gemini_embeddings(text_chunks)
                if not embeddings_with_text:
                    print(f"⚠️ No embeddings generated for {file_path}")
                    continue

                # Store in Qdrant
                success = self.store_in_qdrant(embeddings_with_text)
                if success:
                    print(f"Successfully added {file_path} to Qdrant ✅")
                    self.processed_files.add(
                        str(file_path)
                    )  # Add the string representation
                else:
                    print(f"❌ Failed to add {file_path} to Qdrant")

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

        return len(new_files)


    def extract_text_from_markdown(self, md_files):
        """Extract text from markdown files in the astro_docs directory."""
        print("Extracting text from markdown files...")

        text_chunks = []

        if not md_files:
            print("⚠️ No markdown files provided")
            return (None, [])

        # We expect a *list* of Path objects, even if it's just one.
        if not isinstance(md_files, list) or not all(
            isinstance(f, Path) for f in md_files
        ):
            raise ValueError("md_files must be a list of Path objects")

        # Process only the specified file(s)
        for md_file in md_files:
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                    # Skip empty files
                    if not content.strip():
                        print(f"⚠️ Empty file: {md_file}")
                        continue

                    # Process the content into chunks with overlap
                    chunk_size = 1500
                    chunk_overlap = 250
                    current_position = 0
                    content_length = len(content)

                    while current_position < content_length:
                        end_position = min(
                            current_position + chunk_size, content_length
                        )

                        if end_position < content_length:
                            look_back_range = min(100, chunk_size // 10)
                            natural_break_pos = content.rfind(
                                "\n\n", end_position - look_back_range, end_position
                            )

                            if natural_break_pos != -1:
                                end_position = natural_break_pos
                            else:
                                for punct in [". ", "! ", "? ", "\n"]:
                                    natural_break_pos = content.rfind(
                                        punct,
                                        end_position - look_back_range,
                                        end_position,
                                    )
                                    if natural_break_pos != -1:
                                        end_position = natural_break_pos + 1
                                        break

                        chunk = content[current_position:end_position].strip()

                        if chunk:
                            text_chunks.append(
                                {
                                    "text": chunk,
                                    "source": md_file.name,  # Keep using .name for consistency
                                }
                            )

                        current_position = (
                            end_position - chunk_overlap
                            if end_position < content_length
                            else content_length
                        )

            except Exception as e:
                print(f"❌ Error reading {md_file}: {e}")
                # Return (None, []) on error to signal failure for this file
                return (None, [])

        # Return the *Path object* and the chunks.
        return (md_files[0], text_chunks)

    def generate_gemini_embeddings(self, text_chunks):
        """Generate embeddings for text chunks using Gemini API."""
        print("Generating Gemini embeddings...")

        if not self.genai_client:
            print("❌ Gemini client not initialized. Cannot generate embeddings.")
            return []

        embeddings_with_text = []
        failed_chunks = 0
        batch_size = 10  # Process in batches to avoid overwhelming the API
        requests_per_minute = 150
        delay_between_requests = (
            60.0 / requests_per_minute
        )  # Calculate delay in seconds

        for i in range(0, len(text_chunks), batch_size):
            batch = text_chunks[i : i + batch_size]
            print(
                f"Processing batch {i // batch_size + 1}/{(len(text_chunks) + batch_size - 1) // batch_size}...",
                end="\r",
            )

            for chunk in batch:
                try:
                    # Generate embedding using Gemini
                    result = self.genai_client.models.embed_content(
                        model="gemini-embedding-001", contents=chunk["text"]
                    )

                    # Correctly access the embedding values
                    embedding_values = result.embeddings[
                        0
                    ].values  # Access the first embedding and its values

                    # Add embedding to the chunk data
                    embeddings_with_text.append(
                        {
                            "text": chunk["text"],
                            "source": chunk["source"],
                            "embedding": embedding_values,
                        }
                    )
                    time.sleep(delay_between_requests)  # delay
                except Exception as e:
                    failed_chunks += 1
                    print(
                        f"❌ Error generating embedding for chunk from {chunk['source']}: {e}"
                    )
                    # Continue processing other chunks despite this error

        if failed_chunks > 0:
            print(
                f"⚠️ Failed to generate embeddings for {failed_chunks} chunks out of {len(text_chunks)}"
            )

        print(f"Generated {len(embeddings_with_text)} embeddings ✅")
        return embeddings_with_text

    def store_in_qdrant(self, embeddings_with_text):
        """Store text and embeddings in Qdrant."""
        print(f"Storing embeddings in Qdrant collection '{self.collection_name}'...")

        if not self.qdrant_client:
            print("❌ Qdrant client not initialized. Cannot store embeddings.")
            return False

        try:
            # Check if collection exists and has correct vector size
            vector_size = 3072  # gemini-embedding-001 has 3072 dimensions

            if self.qdrant_client.collection_exists(self.collection_name):
                try:
                    collection_info = self.qdrant_client.get_collection(
                        self.collection_name
                    )
                    existing_vector_size = collection_info.config.params.vectors.size

                    if existing_vector_size != vector_size:
                        print(
                            f"Collection '{self.collection_name}' exists but with incorrect vector size ({existing_vector_size}). Recreating with size {vector_size}."
                        )
                        self.qdrant_client.delete_collection(self.collection_name)
                        create_collection = True
                    else:
                        print(
                            f"Collection '{self.collection_name}' already exists with correct vector size. Updating points."
                        )
                        create_collection = False
                except Exception as e:
                    print(f"❌ Error checking collection info: {e}")
                    print(f"Recreating collection '{self.collection_name}'.")
                    self.qdrant_client.delete_collection(self.collection_name)
                    create_collection = True
            else:
                print(
                    f"Collection '{self.collection_name}' does not exist. Creating it."
                )
                create_collection = True

            # Create collection if needed
            if create_collection:
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size, distance=Distance.COSINE
                    ),
                )

            # Prepare points for Qdrant
            points = []
            for item in embeddings_with_text:
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=item["embedding"],
                        payload={"text": item["text"], "source": item["source"]},
                    )
                )

            # Upload points to Qdrant in batches
            if points:
                batch_size = 100  # Adjust based on your needs
                for i in range(0, len(points), batch_size):
                    batch = points[i : i + batch_size]
                    print(
                        f"Uploading batch {i // batch_size + 1}/{(len(points) + batch_size - 1) // batch_size} to Qdrant...",
                        end="\r",
                    )
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name, points=batch
                    )
                print(f"Successfully stored {len(points)} points in Qdrant ✅")
                return True
            else:
                print("⚠️ No points to store in Qdrant")
                return False

        except Exception as e:
            print(f"❌ Error storing embeddings in Qdrant: {e}")
            print(f"Error details: {str(e)}")  # More detailed error information
            return False
