# CIROH DocuHub Chatbot
The CIROH DocuHub Chatbot is a joint initiative between CIROH and the Alabama Center for the Advancement of Artificial Intelligence (ALAAI), established to lay the foundations for reproducible hydrological research through the development of a lightweight retrieval-augmented generation (RAG) chatbot prototype that connects documentation, workflows, and datasets across CIROH platforms.

Contributors: 
ALAAI: Jiaqi Gong, Shenglin Li, An
CIROH: Arpita Patel, XXXX

## 📖 Overview

Welcome to the CIROH AI Bot repository. This project contains a full-stack application designed to provide a conversational interface to the CIROH documentation. It uses a **Retrieval-Augmented Generation (RAG)** pipeline to answer user questions with accurate, context-aware information sourced directly from the DocuHub knowledge base.

The application consists of two main parts: a **React frontend** for the user interface and a **Python FastAPI backend** that serves the RAG API.

-----

## ▶️ Getting Started: Running the Application (Recommended Path)

This is the quickest way to get the application running. This method connects directly to the existing, populated database hosted on **Azure**, so you do not need to set up a local database or run the data scraping scripts.

### 1\. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/sli90/CIROH-project.git
cd CIROH-project
```

### 2\. Configure the Backend

The backend needs to know how to connect to the Azure database and the OpenAI API. You will do this by creating an environment file.

  * Follow the instructions detailed in the **`backend/rag/README.md`** file to create and configure your `.env` file within the `backend/rag` directory.

### 3\. Run the Backend API

You will need a terminal window for the backend.

```bash
# Navigate to the RAG application directory
cd backend/rag

# Install the required Python packages
pip install -r requirements.txt

### Add `.env` File
Create a `.env` file in both the `rag/` and `database/` directories.  
Include the required environment variables as specified in the `database/` folder documentation.

# Start the API server
uvicorn main:app --reload
```

The API will now be running at `http://1227.0.0.1:8000`.

### 4\. Run the Frontend

You will need a **second, separate terminal window** for the frontend.

```bash
# Navigate to the frontend directory from the project root
cd frontend

# Install the required Node.js packages
npm install

# Start the development server
npm run dev
```

The user interface will now be accessible in your browser at `http://localhost:3000` (or another port specified in the terminal).

-----

## 👨‍💻 For Developers: Full Local Database Replication

This path is intended for developers who need to work on the data pipeline, modify the database schema, or run the entire system locally without relying on the Azure instance. This process is more complex and has significant prerequisites.

**Warning:** This requires a local installation of **PostgreSQL 17** with the **pgvector** extension enabled.

The general workflow is as follows:

1.  **Scrape Content:** Use the scripts in the `backend/CIROH-scraper/` directory to download the latest content from the DocuHub websites.
2.  **Create and Populate Database:** Use the scripts in the `backend/database/` directory to create the database schema, populate it with the scraped content, and generate the vector embeddings for all documents.

For detailed instructions, please refer to the `README.md` files located inside each of those directories.

-----

## 📂 Repository Structure

```
CIROH-AI-Bot/
├── backend/
│   ├── CIROH-scraper/  # Scripts to download content from DocuHub.
│   ├── database/       # Scripts to create and populate a local PostgreSQL DB.
│   ├── rag/            # The core RAG API, logic, and testing notebook.
│   └── azure/          # Informational documentation for future production deployment.
├── frontend/           # The React-based user interface.
└── README.md           # This file.
```

### `backend/`

  * **`CIROH-scraper/`**: Contains Python scripts for scraping and processing content from various CIROH websites. See its internal `README.md` for more details.
  * **`database/`**: Includes SQL schemas and Python scripts to create the PostgreSQL database structure, populate it with data from the scraper, and generate embeddings. See its internal `README.md`.
  * **`rag/`**: The heart of the application. It contains the FastAPI code that serves the AI model, the core RAG logic (`ai_logic.py`), and a Jupyter Notebook (`RAG_Pipeline_Test.ipynb`) for testing the pipeline independently.
  * **`azure/`**: This directory holds documentation and configuration notes related to the future deployment of the application on Azure. Its content is currently for informational purposes only.

### `frontend/`

  * This directory contains the complete React application that provides the chat interface for the AI Bot. Refer to its internal `README.md` for more details on its structure and components.
