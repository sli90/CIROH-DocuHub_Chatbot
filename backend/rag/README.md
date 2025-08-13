# CIROH AI Bot - RAG Pipeline Test

This repository contains a Jupyter Notebook (`RAG_Pipeline_Test.ipynb`) designed to test the Retrieval-Augmented Generation (RAG) pipeline built upon the PostgreSQL database populated by the `PopulateDB.ipynb` script.

The primary purpose of this notebook is to:
1.  Take a list of sample questions.
2.  Generate a vector embedding for each question.
3.  Query the database to find the most relevant document summaries based on semantic similarity.
4.  Construct a prompt that combines the user's question with the retrieved context.
5.  Send the prompt to an LLM (Large Language Model) to generate a final, context-aware answer.
6.  Display the retrieved sources (as breadcrumbs) for transparency and verification.

---

## Prerequisites

Before running this notebook, you **must** have already:
1.  Completed all the steps in the database `README.md` file.
2.  Successfully run the `PopulateDB.ipynb` notebook to populate your PostgreSQL database with summaries and embeddings.
3.  Ensured your `.env` file is correctly configured with your database and OpenAI API credentials.

---

## ▶️ Running the RAG Test

1.  Ensure your Anaconda (or other Python) environment is activated.
2.  Start the Jupyter Notebook server:
    ```bash
    jupyter notebook
    ```
3.  Open the `RAG_Pipeline_Test.ipynb` file in your browser.
4.  Run the cells sequentially. The notebook will execute the RAG pipeline for each of the predefined test questions and print the results, including the retrieved context, the final answer, and the sources.

---

## ⚙️ How the RAG Pipeline Works

The pipeline follows these key steps for each question:

1.  **Generate Question Embedding**: The user's question is converted into a 1536-dimension vector using the OpenAI embedding model.
2.  **Retrieve Context**: This vector is used to query the `tblurls` table in the PostgreSQL database. The query uses the cosine similarity operator (`<=>`) on the `embedding` column to find the top 3 most semantically similar document summaries.
3.  **Build Prompt**: A carefully crafted prompt is constructed, instructing the LLM to answer the original question based *only* on the context retrieved from the database. This prevents the model from using external knowledge and reduces "hallucinations."
4.  **Generate Final Answer**: The complete prompt is sent to the LLM (e.g., `gpt-5`), which synthesizes the information from the context to generate a direct answer to the user's question.
5.  **Cite Sources**: To ensure transparency, the system retrieves the breadcrumb trails for the source documents and displays them alongside the final answer.

