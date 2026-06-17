import os
import io
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient # pyright: ignore[reportMissingImports]
from qdrant_client.http import models  # pyright: ignore[reportMissingImports] # Ensured compatibility import
from pypdf import PdfReader # pyright: ignore[reportMissingImports]
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Document Sandbox Engine (Gemini + Qdrant)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "knowledge_base"

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

try:
    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="session_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    print("✅ Qdrant session isolation mapping layer index verified.")
except Exception as e:
    pass


# 👇 NEW HELPER FUNCTION: SLIDING WINDOW CHUNKING
def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Splits a long string of text into smaller overlapping segments."""
    chunks = []
    if not text:
        return chunks
        
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        # Move the window forward by chunk_size minus the overlap
        start += chunk_size - overlap
        
        # Guard against infinite loops if sizes are misconfigured
        if chunk_size <= overlap:
            break
            
    return chunks


class DocumentInput(BaseModel):
    text: str
    session_id: str

class QueryInput(BaseModel):
    text: str
    session_id: str


# Endpoint A: Plain-Text Uploads (Now with Chunking!)
@app.post("/upload")
async def upload_document(doc: DocumentInput):
    try:
        # Split text into bite-sized paragraphs
        text_chunks = chunk_text(doc.text)
        
        # Create matching metadata lists for every single chunk
        metadata_list = [{"session_id": doc.session_id} for _ in text_chunks]
        
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=text_chunks,
            metadata=metadata_list
        )
        return {"status": "success", "message": f"Text fragmented into {len(text_chunks)} chunks and bound successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint B: Multi-page Binary PDF Parsing (Now with Chunking!)
@app.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a standard PDF.")

        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        reader = PdfReader(pdf_file)
        
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="This PDF contains no machine-readable text characters.")

        # 👇 Chunk the entire extracted book/paper text string
        text_chunks = chunk_text(extracted_text)
        metadata_list = [{"session_id": session_id} for _ in text_chunks]

        # Ingest chunks collectively
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=text_chunks,
            metadata=metadata_list
        )

        return {
            "status": "success", 
            "message": f"Successfully parsed {len(reader.pages)} pages and split into {len(text_chunks)} searchable vectors."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint C: Isolated RAG Retrieval and Synthesis Engine (Stays identical)
@app.post("/query")
async def query_and_generate(query: QueryInput):
    try:
        search_results = qdrant_client.query(
            collection_name=COLLECTION_NAME,
            query_text=query.text,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="session_id",
                        match=models.MatchValue(value=query.session_id),
                    )
                ]
            ),
            limit=3  # Will now pull the top 3 most relevant chunks instead of whole documents!
        )
        
        retrieved_contexts = [point.document for point in search_results if point.document]
        context_str = "\n---\n".join(retrieved_contexts)
        
        if not retrieved_contexts:
            context_str = "No specific reference documents found inside this isolated canvas environment."

        system_instruction = (
            "You are a precise, technical AI sandbox assistant. Answer the user's prompt query "
            "using ONLY the localized context provided below. If the answer cannot be determined "
            "directly from the context facts, explicitly state that no context records match.\n\n"
            f"Context:\n{context_str}"
        )

        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=query.text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            )
        )
            
        return {
            "query": query.text, 
            "answer": response.text, 
            "sources": retrieved_contexts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Add this endpoint alongside your other routing blocks in main.py
@app.post("/clear-session")
async def clear_session_data(query: QueryInput):
    try:
        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="session_id",
                            match=models.MatchValue(value=query.session_id),
                        )
                    ]
                )
            ),
        )
        return {"status": "success", "message": "All session data points cleared simultaneously."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))