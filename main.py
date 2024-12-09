from fastapi import FastAPI, UploadFile, HTTPException, Depends, BackgroundTasks
import os
import shutil
import io
from db import get_db, File, FileChunk
from sqlalchemy.orm import Session
from file_parser import FileParser
from background_tasks import TextProcessor, client as client2
from sqlalchemy import select
from pydantic import BaseModel
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage
from azure.ai.inference.models import UserMessage
from azure.core.credentials import AzureKeyCredential

app = FastAPI()

load_dotenv()


class QuestionModel(BaseModel):
    question: str


class AskModel(BaseModel):
    document_id: int
    question: str


@app.get("/")
async def root(db: Session = Depends(get_db)):
    # Query the database for all files
    files_query = select(File)
    files = db.scalars(files_query).all()

    # Format and return the list of files including file_id and filename
    files_list = [
        {"file_id": file.file_id, "file_name": file.file_name} for file in files
    ]
    return files_list


@app.post("/uploadfile/")
async def upload_file(
    background_tasks: BackgroundTasks, file: UploadFile, db: Session = Depends(get_db)
):  
    # Define allowed file extensions
    allowed_extensions = ["txt", "pdf", "docx", "md", "png", "jpg", "jpeg"]

    # Check if the file extension is allowed
    file_extension = file.filename.split(".")[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Create the folder if it doesn't exist
    folder = "sources"
    try:
        # Ensure the directory exists
        os.makedirs(folder, exist_ok=True)

        # Secure way to save the file
        file_location = os.path.join(folder, file.filename)
        file_content = await file.read()  # Read file content as bytes
        with open(file_location, "wb+") as file_object:
            # Convert bytes content to a file-like object
            file_like_object = io.BytesIO(file_content)
            # Use shutil.copyfileobj for secure file writing
            shutil.copyfileobj(file_like_object, file_object)

        content_parser = FileParser(file_location)
        file_text_content = content_parser.parse()

        # save file details in the database
        new_file = File(file_name=file.filename, file_content=file_text_content)
        db.add(new_file)
        db.commit()
        db.refresh(new_file)

        # Add background job for processing file content
        background_tasks.add_task(
            TextProcessor(db, new_file.file_id).chunk_and_embed, file_text_content
        )  

        return {"message": "File saved", "filename": file.filename}

    except Exception as e:
        # Log the exception (add actual logging in production code)
        print(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")


# Function to get similar chunks
async def get_similar_chunks(file_id: int, question: str, db: Session):
    try:
        # Create embeddings for the question (assuming client and embedding creation logic)
        response = client2.embeddings.create(
            input=question, model="text-embedding-3-small"
        )
        question_embedding = response.data[0].embedding

        similar_chunks_query = (
            select(FileChunk)
            .where(FileChunk.file_id == file_id)
            .order_by(FileChunk.embedding_vector.l2_distance(question_embedding))
            .limit(10)
        )
        similar_chunks = db.scalars(similar_chunks_query).all()

        return similar_chunks

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/")
async def ask_question(request: AskModel, db: Session = Depends(get_db)):
    TOKEN = os.getenv("GITHUB_TOKEN")

    client = ChatCompletionsClient(
        endpoint="https://models.inference.ai.azure.com",
        credential=AzureKeyCredential(TOKEN),
    )

    if TOKEN is None:
        raise HTTPException(status_code=500, detail="TOKEN not found")
    try:
        similar_chunks = await get_similar_chunks(
            request.document_id, request.question, db
        )

        # Construct context from the similar chunks' texts
        context_texts = [chunk.chunk_text for chunk in similar_chunks]
        context = " ".join(context_texts)

        # Update the system message with the context
        system_message = (
            f"You are an assistant designed to provide accurate and helpful responses strictly based on the given context. "
            f"If a user's question is not addressed by the provided context, respond with: "
            f"`I'm sorry, I don't have relevant information on that!` "
            f"Do not mention that you have been provided with the context."
            f"Here is the context for your responses: {context}"
        )

        # Call the completion endpoint with the system message and user question
        response = client.complete(
            messages=[
                SystemMessage(content=system_message),
                UserMessage(content=request.question),
            ],
            model="Mistral-large-2407",
            temperature=0.8,
            max_tokens=4096,
            top_p=0.1,
        )

        return {"response": response.choices[0].message.content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


