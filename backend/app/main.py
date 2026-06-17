import os
import io
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient # pyright: ignore[reportMissingImports]
from qdrant_client.http import models # pyright: ignore[reportMissingImports]
from pypdf import PdfReader # pyright: ignore[reportMissingImports]
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load secret tokens out of local environment configuration file
load_dotenv()

app = FastAPI(title="Document Sandbox Engine (Gemini + Qdrant)")

# Configure CORS so your frontend development pipeline can securely pass assets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pull environment cluster routing flags
QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "knowledge_base"

# Ensure all variables are bound
if not all([QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY]):
    print("⚠️ CRITICAL WARNING: Please verify that your .env file contains valid host and authorization keys!")

# Instantiate engine clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# 🛠️ Structural Payload Indexing Setup
try:
    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="session_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    print("✅ Qdrant session isolation mapping layer index verified.")
except Exception as e:
    pass


# Pydantic Schemas mapping incoming application JSON packets
class DocumentInput(BaseModel):
    text: str
    session_id: str

class QueryInput(BaseModel):
    text: str
    session_id: str


# Endpoint A: Pure Plain-Text Uploads
@app.post("/upload")
async def upload_document(doc: DocumentInput):
    try:
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=[doc.text],
            metadata=[{"session_id": doc.session_id}]
        )
        return {"status": "success", "message": "Text data fragment bound successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint B: Multi-page Binary PDF Parsing
@app.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a standard PDF.")

        # Stream binary bytes into reader memory
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

        # Ingest parsed structural contents under session key
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=[extracted_text],
            metadata=[{"session_id": session_id}]
        )

        return {
            "status": "success", 
            "message": f"Successfully parsed and vectorized {len(reader.pages)} pages from {file.filename}."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint C: Isolated RAG Retrieval and Synthesis Engine
@app.post("/query")
async def query_and_generate(query: QueryInput):
    try:
        # 1. RETRIEVAL: Pull vectors matching user's specific session token
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

        # 2. GENERATION: Inject factual guardrails to Gemini
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