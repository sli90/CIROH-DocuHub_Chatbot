# CIROH AI Bot - RAG Pipeline

This document provides instructions for setting up and running the CIROH AI Bot Retrieval-Augmented Generation (RAG) pipeline, a full-stack application designed to answer questions about CIROH documentation.

The RAG pipeline consists of three main components:

  * **React Frontend**: A user-friendly chat interface.
  * **Python FastAPI Backend**: An API that executes the RAG pipeline.
  * **Azure PostgreSQL Database**: A cloud-hosted database containing the vectorized documentation.

-----

## ⚙️ Configuration and Setup

To run the application, you first need to configure the backend's environment variables.

1.  Navigate to the `backend/rag` directory within the project.
2.  Create a new file in this directory named `.env`.
3.  Copy and paste the following content into your new `.env` file. This configuration connects the application to the shared Azure database with a **read-only user**.

<!-- end list -->

```env
# backend/rag/.env

# Azure PostgreSQL Database Credentials (Read-Only Access)
POSTGRES_HOST="c-ciroh-cluster.6cijvkzzmrtw2p.postgres.cosmos.azure.com"
POSTGRES_DB="ciroh"
POSTGRES_USER="raguser"
POSTGRES_PASSWORD="CIROH_0028837733"

# OpenAI API Credentials
# Replace "sk-..." with your actual OpenAI API key
OPENAI_API_KEY="sk-..."
EMBEDDING_MODEL="text-embedding-3-large"
```

-----

## ▶️ Running the Application

To run the application, you need to start the backend API and the frontend UI in **two separate terminals**.

### 1\. Start the Backend (FastAPI API)

In your first terminal, run the following commands:

```bash
# Navigate to the RAG application directory
cd backend/rag

# Install the required Python packages
pip install -r requirements.txt

# Start the API server from this directory
uvicorn main:app --reload
```

The API will now be running at `http://127.0.0.1:8000`.

### 2\. Start the Frontend (React App)

In your second terminal:

```bash
# Navigate to the frontend directory from the project root
cd frontend

# Install the required Node.js packages
npm install

# Start the development server
npm run dev
```

The user interface will now be accessible in your browser at `http://localhost:3000`.

-----

## 🧠 How the RAG Pipeline Works

The pipeline follows these key steps for each question:

1.  **Generate Question Embedding**: The user's question is converted into a vector using an OpenAI embedding model.
2.  **Retrieve Context**: This vector is used to query the Azure PostgreSQL database. The query uses vector similarity search to find the most semantically similar document chunks.
3.  **Build Prompt**: A carefully crafted prompt is constructed, instructing the LLM to answer the original question based *only* on the context retrieved from the database. This prevents the model from using external knowledge and reduces "hallucinations."
4.  **Generate Final Answer**: The complete prompt is sent to the LLM, which synthesizes the information from the context to generate a direct answer.
5.  **Cite Sources**: To ensure transparency, the system retrieves the breadcrumb trails for the source documents and displays them alongside the final answer.