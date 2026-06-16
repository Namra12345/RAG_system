import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient, models # pyright: ignore[reportMissingImports]
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load key variables out of the local secret .env file
load_dotenv()

app = FastAPI(title="Session Isolated Gemini RAG Engine")

# Configure CORS Middleware globally so your React App (Vite) can reach it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Grab target environment parameters
QDRANT_URL = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
COLLECTION_NAME = "knowledge_base"

# Ensure crucial variables exist before executing connection setups
if not all([QDRANT_URL, QDRANT_API_KEY, GEMINI_API_KEY]):
    print("⚠️ WARNING: One or more required environment keys are missing inside your .env file!")

# Initialize target cloud framework instances
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
genai_client = genai.Client(api_key=GEMINI_API_KEY)

# 🛠️ AUTO-CREATE FIELD PAYLOAD INDEX FOR FILTER SCHEMAS
try:
    qdrant_client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="session_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    print("✅ Qdrant 'session_id' payload keyword index verified and configured.")
except Exception as e:
    # If the index configuration structure already exists, bypass gracefully
    pass

# Data Transfer Pydantic Schemas mapping incoming network requests
class DocumentInput(BaseModel):
    text: str
    session_id: str

class QueryInput(BaseModel):
    text: str
    session_id: str


@app.post("/upload")
async def upload_document(doc: DocumentInput):
    try:
        # Vectorize text on CPU threads via fastembed and save under isolated session labels
        qdrant_client.add(
            collection_name=COLLECTION_NAME,
            documents=[doc.text],
            metadata=[{"session_id": doc.session_id}]
        )
        return {"status": "success", "message": "Information segment ingested into session context."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def query_and_generate(query: QueryInput):
    try:
        # 1. RETRIEVAL: Pull semantic fragments strictly matching user's specific session_id
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
        
        # Consolidate retrieved strings into structured string arrays
        retrieved_contexts = [point.document for point in search_results if point.document]
        context_str = "\n---\n".join(retrieved_contexts)
        
        if not retrieved_contexts:
            context_str = "No applicable factual references found inside your active sandbox canvas session."

        # 2. GENERATION: Inject exact boundary rules and facts directly to Gemini 2.5 Flash
        system_instruction = (
            "You are a strict, precise AI sandbox assistant. Answer the user's prompt query "
            "using ONLY the localized context provided below. If the answer cannot be determined "
            "directly from the context facts, explicitly state that no context records match.\n\n"
            f"Context:\n{context_str}"
        )

        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=query.text,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2, # Lower values prevent hallucination bleeding
            )
        )
            
        return {
            "query": query.text, 
            "answer": response.text, 
            "sources": retrieved_contexts
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))