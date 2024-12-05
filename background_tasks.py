import os
from openai import OpenAI
from sqlalchemy.orm import Session
from db import FileChunk
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv

load_dotenv()


endpoint = "https://models.inference.ai.azure.com"
OPENAI_API_KEY = os.getenv("GITHUB_TOKEN")
if not OPENAI_API_KEY:
    raise ValueError("Token is not set in the environment variables.")

model_name = "text-embedding-3-small"

client = OpenAI(base_url=endpoint, api_key=OPENAI_API_KEY)

# Make sure to run the nltk.sh script to download the necessary nltk data


class TextProcessor:
    def __init__(self, db: Session, file_id: int, chunk_size: int = 2):
        self.db = db
        self.file_id = file_id
        self.chunk_size = chunk_size

    def chunk_and_embed(self, text: str):
        try:
            # Split text into sentences
            try:
                sentences = sent_tokenize(text)
                print(f"Successfully tokenized {len(sentences)} sentences")
            except Exception as e:
                print(f"Error tokenizing sentences: {e}")
                raise

            # Chunk sentences
            try:
                chunks = [
                    " ".join(sentences[i : i + self.chunk_size])
                    for i in range(0, len(sentences), self.chunk_size)
                ]
                print(f"Successfully chunked into {len(chunks)} chunks")
            except Exception as e:
                print(f"Error chunking sentences: {e}")
                raise

            for chunk in chunks:
                try:
                    # Create embeddings
                    response = client.embeddings.create(input=chunk, model=model_name)
                    embeddings = response.data[0].embedding

                    # Store chunk and embedding in database
                    file_chunk = FileChunk(
                        file_id=self.file_id,
                        chunk_text=chunk,
                        embedding_vector=embeddings,
                    )
                    self.db.add(file_chunk)
                    print(f"Successfully processed chunk: {chunk[:50]}...")
                except Exception as e:
                    print(f"Error processing chunk: {e}")
                    raise

            try:
                self.db.commit()
                print("Successfully committed to database")
            except Exception as e:
                print(f"Error committing to database: {e}")
                self.db.rollback()
                raise
        except Exception as e:
            print(f"Fatal error in chunk_and_embed: {e}")
            raise
