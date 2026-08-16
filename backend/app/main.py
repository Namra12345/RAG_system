import os
import io
import asyncio
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient # pyright: ignore[reportMissingImports]
from qdrant_client.http import models # pyright: ignore[reportMissingImports]
from pypdf import PdfReader # pyright: ignore[reportMissingImports]
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "knowledge_base"

qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# Track last activity timestamp per session
session_timestamps = {}


def setup_qdrant_indexing():
    """Ensure payload index for session_id exists on the Qdrant collection."""
    try:
        collections = [c.name for c in qdrant_client.get_collections().collections]
        
        # Verify collection exists before attempting index creation
        if COLLECTION_NAME in collections:
            qdrant_client.create_payload_index(
                collection_name=COLLECTION_NAME,
                field_name="session_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
            print("✅ Qdrant session isolation payload index verified.")
        else:
            print("ℹ️ Collection does not exist yet. Will auto-create on first vector ingest.")
    except Exception as e:
        print(f"⚠️ Payload Index Setup Note: {e}")


async def auto_purge_expired_sessions():
    """Background task to delete vector data older than 24 hours."""
    while True:
        try:
            await asyncio.sleep(1800) # Run every 30 mins
            now = datetime.now(timezone.utc)
            expired_sessions = [
                sid for sid, last_active in list(session_timestamps.items())
                if now - last_active > timedelta(hours=24)
            ]
            
            for session_id in expired_sessions:
                print(f"🧹 Purging abandoned session: {session_id}")
                qdrant_client.delete(
                    collection_name=COLLECTION_NAME,
                    points_selector=models.FilterSelector(
                        filter=models.Filter(
                            must=[
                                models.FieldCondition(
                                    key="session_id",
                                    match=models.MatchValue(value=session_id),
                                )
                            ]
                        )
                    ),
                )
                session_timestamps.pop(session_id, None)
                
            if expired_sessions:
                print(f"✅ Cleaned up {len(expired_sessions)} stagnant session(s).")
        except Exception as e:
            print(f"⚠️ Error running background auto-purge task: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    setup_qdrant_indexing()
    purge_task = asyncio.create_task(auto_purge_expired_sessions())
    print("🚀 Auto-Purge background worker initialized.")
    yield
    # Cleanup tasks
    purge_task.cancel()


app = FastAPI(title="Document Sandbox Engine with Auto-TTL", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    if not text:
        return chunks
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
        if chunk_size <= overlap:
            break
    return chunks


class DocumentInput(BaseModel):
    text: str
    session_id: str

class QueryInput(BaseModel):
    text: str
    session_id: str


@app.post("/upload")
async def upload_document(doc: DocumentInput):
    try:
        session_timestamps[doc.session_id] = datetime.now(timezone.utc)
        text_chunks = chunk_text(doc.text)
        metadata_list = [{"session_id": doc.session_id} for _ in text_chunks]
        
        # High-level API handles schema creation natively
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=text_chunks,
            metadata=metadata_list
        )
        
        # Verify payload index is present right after insertion
        setup_qdrant_indexing()

        return {"status": "success", "message": f"Text fragmented into {len(text_chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    try:
        session_timestamps[session_id] = datetime.now(timezone.utc)

        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Unsupported file format.")

        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        reader = PdfReader(pdf_file)
        
        extracted_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="PDF contains no readable text.")

        text_chunks = chunk_text(extracted_text)
        metadata_list = [{"session_id": session_id} for _ in text_chunks]

        # High-level API handles schema creation natively
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=text_chunks,
            metadata=metadata_list
        )

        # Verify payload index is present right after insertion
        setup_qdrant_indexing()

        return {
            "status": "success", 
            "message": f"Parsed {len(reader.pages)} pages into {len(text_chunks)} searchable vectors."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        session_timestamps.pop(query.session_id, None)
        return {"status": "success", "message": "All session data points cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_and_generate(query: QueryInput):
    try:
        if query.session_id in session_timestamps:
            session_timestamps[query.session_id] = datetime.now(timezone.utc)

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
            limit=3
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