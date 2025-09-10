# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# Import the main function from your AI logic
from ai_logic import generate_answer_from_question

# Define the data model for the question coming from the frontend
class Question(BaseModel):
    text: str

app = FastAPI(
    title="CIROH AI Bot API",
    description="API for the CIROH DocuHub AI assistant"
)

# CORS configuration to allow requests from your frontend
origins = [
    "http://localhost:3000",  # Default port for React
    "http://127.0.0.1:3000",  # Default port for React
    "http://localhost:5173",  # Default port for Vite/React
    "http://127.0.0.1:5173",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health Check"])
def read_root():
    """Root endpoint to check if the API is running."""
    return {"status": "CIROH AI Bot API is running"}

@app.post("/ask", tags=["AI Assistant"])
async def ask_ai(question: Question):
    """
    Receives a user's question, processes it with the RAG pipeline,
    and returns the answer and sources.
    """
    # Call the function that contains all the complex logic
    result = generate_answer_from_question(question.text)
    
    # Return the result directly
    return result