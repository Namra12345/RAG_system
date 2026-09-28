# RAG System Deployed With DevOps Practices

This project is a Retrieval-Augmented Generation (RAG) application built as a full-stack system with a frontend, backend API, vector database, and AI-powered answer generation. The solution is designed to demonstrate standard DevOps practices including containerization, infrastructure-as-code, AWS provisioning, and deployment automation.

The application lets users upload text or PDF documents, split them into searchable chunks, store them in a vector database, and then ask questions only against the data stored in their own isolated session. The backend retrieves relevant chunks and sends them to Google Gemini for grounded answer generation.

---

## 1. Project Overview

This repository contains:

- A React frontend for user interaction
- A FastAPI backend for document ingestion and Q&A
- Qdrant as the vector database for semantic retrieval
- Google Gemini 2.5 Flash for answer generation
- Docker containers for environment consistency
- Terraform modules for AWS infrastructure provisioning
- Docker Compose for local or server-based orchestration

The design follows a common DevOps pattern:

1. Code is organized into separate application layers
2. Applications are containerized with Docker
3. Infrastructure is defined with Terraform
4. Services are deployed to AWS EC2
5. Images are stored in Amazon ECR
6. Runtime configuration is managed through environment variables

---

## 2. Architecture

### Frontend
- Built with React and Vite
- Runs on port 5173 in the container
- Provides a user interface where users can:
  - paste text
  - upload PDF files
  - ask questions
  - clear the active session

### Backend
- Built with FastAPI
- Runs on port 8000
- Exposes endpoints for:
  - /upload
  - /upload-file
  - /query
  - /clear-session
- Handles chunking, document parsing, session-aware retrieval, and LLM orchestration

### Vector Database
- Uses Qdrant for storing document chunks and metadata
- Each chunk is stored with a session_id so data stays isolated to one user/session
- Retrieval is filtered by session_id before a query is answered

### AI Layer
- Uses Google Gemini through the Google GenAI SDK
- Query responses are grounded in retrieved context from Qdrant
- The model is prompted with a system instruction that restricts it to the uploaded context

### Infrastructure / DevOps Layer
- Dockerfiles define the backend and frontend images
- Docker Compose defines the multi-container runtime stack
- Terraform creates the AWS resources:
  - VPC
  - ECR repositories
  - EC2 instance
  - security groups
  - IAM role for ECR access

---

## 3. Key Features

### Document ingestion
- Users can upload raw text directly into the application
- Users can upload PDF files and extract readable content from pages
- Content is split into chunks using an overlapping chunking strategy to preserve context

### Session isolation
- Every session receives a unique session_id
- Vector data is tagged with that session_id
- Queries only search inside that session’s indexed data
- Old sessions can be automatically purged after a TTL period

### Retrieval-augmented generation
- Relevant text chunks are retrieved from Qdrant using the user’s question
- The retrieved context is sent to Gemini as the reference material
- The model answers only from the local context rather than from general knowledge alone

### Automatic cleanup
- A background task monitors session activity
- Sessions older than 24 hours are removed from Qdrant automatically
- This avoids stale data accumulating in the vector store

### PDF support
- The backend parses PDF pages using pypdf
- Text is extracted and prepared for vector indexing and retrieval

### DevOps-ready deployment
- Dockerized services for portability
- Terraform-managed AWS provisioning
- ECR image hosting for frontend/backend
- EC2 instance automation with Docker installation

---

## 4. Project Structure

```text
RAG_system/
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── providers.tf
│   └── modules/
│       ├── vpc/
│       ├── ecr/
│       └── ec2/
├── docker-compose.yml
├── README.md
└── LICENSE
```

---

## 5. How the Project Is Built Step by Step

### Step 1: Set up the development environment
The project depends on Python, Node.js, Docker, Terraform, and cloud credentials.

Required tools:
- Python 3.13
- Node.js 20+
- Docker and Docker Compose
- Terraform
- AWS CLI
- An AWS account
- Qdrant access
- A Google Gemini API key

### Step 2: Configure environment variables
The backend reads secrets and connection settings from environment variables.

Example:

```env
QDRANT_HOST=https://your-qdrant-instance.example.com
QDRANT_API_KEY=your_qdrant_api_key
GEMINI_API_KEY=your_gemini_api_key
AWS_ACCOUNT_ID=123456789012
```

These values are used by the backend API at runtime.

### Step 3: Build the backend service
The backend container is defined in backend/Dockerfile.

It:
- starts from a Python 3.13 slim image
- installs dependencies from requirements.txt
- copies the FastAPI application into the container
- exposes port 8000
- runs Uvicorn to serve the API

The backend handles document ingestion, indexing, and query processing.

### Step 4: Build the frontend service
The frontend container is defined in frontend/Dockerfile.

It:
- starts from a Node 20 Alpine image
- runs npm install
- copies the React application into the container
- exposes port 5173
- starts Vite in host mode for browser access

This keeps the frontend separated from the backend and allows clean service communication.

### Step 5: Define the runtime stack with Docker Compose
The root docker-compose.yml defines the application stack.

It runs:
- the backend container on port 8000
- the frontend container on port 80 mapped to the Vite app port 5173
- environment variables loaded from .env
- dependency ordering so the frontend starts after the backend

This is a standard containerized deployment pattern for local or server-based deployment.

### Step 6: Provision AWS infrastructure with Terraform
The Terraform project in the terraform folder provisions the cloud resources needed for deployment.

Typical commands:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

What Terraform creates:
- VPC for network isolation
- ECR repositories for container images
- EC2 instance for running the app
- security groups for SSH, HTTP, and backend access
- IAM role for ECR access

The EC2 instance installs Docker and Docker Compose automatically using user_data.

### Step 7: Build and push Docker images to ECR
Once infrastructure is ready, the images are built and pushed for deployment.

Typical flow:

```bash
docker build -t rag-app-backend ./backend
docker build -t rag-app-frontend ./frontend
```

Then tag and push them into the AWS ECR repositories configured by Terraform.

This follows standard DevOps practice where deployment happens through container images instead of direct host configuration.

### Step 8: Deploy containers on the EC2 instance
After the EC2 instance is active, the system can pull the images from ECR and run the app containers.

Example deployment pattern:

```bash
sudo docker login <aws-account>.dkr.ecr.us-east-1.amazonaws.com
sudo docker pull <ecr-repo>/rag-app-backend:latest
sudo docker pull <ecr-repo>/rag-app-frontend:latest
sudo docker compose up -d
```

This is the real-world deployment model used by the project in AWS.

---

## 6. How the Application Works at Runtime

### User flow
1. A user opens the frontend UI
2. The user enters text or uploads a PDF
3. The backend splits content into chunks
4. Each chunk is stored in Qdrant with a session_id
5. The user asks a query in the same session
6. The backend filters retrieval to that session only
7. Matching chunks are returned
8. Gemini generates an answer based on those chunks

### Session handling
The backend tracks activity timestamps for each session and performs periodic cleanup so stale documents are removed after inactivity. This gives the app a temporary knowledge-canvas behavior instead of a permanent global document store.

---

## 7. Benefits of This Project

This project demonstrates several important engineering practices:

- Full-stack app architecture
- RAG pipeline implementation
- Document ingestion with PDF parsing
- Semantic retrieval with Qdrant
- LLM-powered answer generation
- Session-based isolation and cleanup
- Dockerized deployment
- Secure AWS provisioning with Terraform
- DevOps-oriented deployment workflow

---

## 8. Typical Development and Deployment Commands

### Local app run with Docker Compose
```bash
docker compose up --build
```

### Frontend-only development
```bash
cd frontend
npm install
npm run dev
```

### Backend-only development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terraform deployment
```bash
cd terraform
terraform init
terraform validate
terraform plan
terraform apply
```

---

## 9. Summary

This project is a practical example of a production-style RAG system using modern DevOps practices. It combines AI retrieval, document processing, cloud infrastructure automation, and container-based deployment in one working solution.

It represents a strong example of how a document Q&A application can be built with:
- a React frontend
- a Python backend
- vector search for retrieval
- an LLM for grounded responses
- infrastructure automation for real deployment

Potential future improvements include:
- user authentication
- persistent document storage
- configurable model selection
- CI/CD integration with GitHub Actions
- application monitoring and observability