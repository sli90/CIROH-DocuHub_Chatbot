# ai_logic.py

import os
import openai
import psycopg2
from dotenv import load_dotenv

# --- INITIALIZATION (runs once when the server starts) ---

# Load environment variables from the .env file
load_dotenv()

# Configuration and Clients
PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")

print("Initializing database connection and OpenAI client...")

# Database connection (kept open while the app is running)
try:
    conn = psycopg2.connect(
        host=PG_HOST, database=PG_DB, user=PG_USER, password=PG_PASS
    )
    print("✅ Database connection established.")
except Exception as e:
    print(f"❌ Error connecting to the database: {e}")
    conn = None

# OpenAI Client
try:
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    print("✅ OpenAI client initialized.")
except Exception as e:
    print(f"❌ Error initializing OpenAI client: {e}")
    client = None

# --- HELPER FUNCTIONS ---

def execute_query(db_conn, query, params=None, fetch=False):
    """Safely executes a SQL query."""
    if not db_conn:
        print("Error: Database connection is not available.")
        return None
    try:
        with db_conn.cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            else:
                db_conn.commit()
    except Exception as e:
        print(f"Error executing query: {e}")
        db_conn.rollback()
        return None


def get_breadcrumb(db_conn, url_id):
    """Generates the breadcrumb for a given idurl."""
    query = """
    WITH RECURSIVE breadcrumb_path AS (
        SELECT idurl, name, idurlparent, 1 AS depth FROM tblurls WHERE idurl = %s
        UNION ALL
        SELECT u.idurl, u.name, u.idurlparent, bp.depth + 1 FROM tblurls u JOIN breadcrumb_path bp ON u.idurl = bp.idurlparent
    )
    SELECT string_agg(name, ' > ' ORDER BY depth DESC) AS breadcrumb FROM breadcrumb_path;
    """
    result = execute_query(db_conn, query, params=(url_id,), fetch=True)
    return result[0][0] if result and result[0] else None

def get_url_trail(db_conn, url_id):
    """Generates the URL trail for a given idurl."""
    query = """
    WITH RECURSIVE breadcrumb_path AS (
        SELECT idurl, name, url, idurlparent, 1 AS depth FROM tblurls WHERE idurl = %s
        UNION ALL
        SELECT u.idurl, u.name, u.url, u.idurlparent, bp.depth + 1 FROM tblurls u JOIN breadcrumb_path bp ON u.idurl = bp.idurlparent
    )
    SELECT string_agg(url, ' > ' ORDER BY depth DESC) AS url_trail FROM breadcrumb_path;
    """
    result = execute_query(db_conn, query, params=(url_id,), fetch=True)
    return result[0][0] if result and result[0] else None


def get_embedding(text, dimensions, model=EMBEDDING_MODEL):
    """Gets the embedding for a text using OpenAI."""
    try:
        response = openai.embeddings.create(
            input=text,
            model=model,
            dimensions=dimensions
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return None


def query_embedding(db_conn, question_embedding, max_relevant_urls=3):
    """Queries the database for the most relevant summaries."""
    query = """
        SELECT idurl, summary_data ->> 'summary_text' as summary
        FROM tblurls WHERE summary_data IS NOT NULL
        ORDER BY embedding <=> %s::vector LIMIT %s
    """
    return execute_query(
        db_conn, query, params=(question_embedding, max_relevant_urls), fetch=True
    )


def query_chunks(db_conn, question_embedding, relevant_url_ids, max_relevant_chunks=5):
    """Queries for the most relevant chunks within a list of pages."""
    query = """
        SELECT idurl, "order", Content FROM TBLContent
        WHERE idurl = ANY(%s) ORDER BY embedding <=> %s::vector LIMIT %s;
    """
    return execute_query(
        db_conn,
        query,
        params=(relevant_url_ids, question_embedding, max_relevant_chunks),
        fetch=True,
    )


def build_rag_prompt(question, context_summaries):
    """Builds the prompt for the LLM."""
    context_str = "\n\n---\n\n".join(context_summaries)
    return f"""
You are an expert AI assistant for the CIROH DocuHub. Your task is to answer the user's question based *only* on the provided context.

If the context does not contain the answer, state that you cannot answer the question with the information given. Do not use any external knowledge.

**CONTEXT:**
---
{context_str}
---

**QUESTION:**
{question}

**ANSWER:**
"""


def get_rag_answer(prompt):
    """Calls the LLM to generate the final answer."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Error generating RAG answer: {e}")
        return "Sorry, an error occurred while generating the response."


# --- MAIN PIPELINE FUNCTION ---


def generate_answer_from_question(question: str) -> dict:
    """
    This is the main function that encapsulates the entire RAG pipeline.
    It receives a question and returns a dictionary with the answer and sources.
    """
    if not conn or not client:
        return {
            "answer": "The service is currently unavailable due to a configuration issue.",
            "sources": [],
            "links": []
        }


    # Pipeline parameters
    max_relevant_urls = 5
    max_relevant_chunks = 10


    # 1. Get the embedding for the question
    question_embedding = get_embedding(question, dimensions=1792)
    if question_embedding is None:
        return {"answer": "Could not process the question.", "sources": [], "links": []}

    # 2. Level 1 Search: Find relevant pages
    retrieved_pages = query_embedding(conn, question_embedding, max_relevant_urls)
    if not retrieved_pages:
        return {
            "answer": "No relevant information was found to answer your question.",
            "sources": [],
            "links": []
        }

    page_summary_map = {row[0]: row[1] for row in retrieved_pages}
    context_ids = list(page_summary_map.keys())

    # 3. Level 2 Search: Find relevant chunks within those pages
    retrieved_chunks = query_chunks(conn, question_embedding, context_ids, max_relevant_chunks)

    final_context_list = []
    source_ids = []

    if not retrieved_chunks:
        # If no chunks are found, use the page summaries as context
        final_context_list = list(page_summary_map.values())
        source_ids = context_ids
    else:
        # Logic to build an enriched context from the chunks
        chunks_by_page = {}
        for idurl, order, content in retrieved_chunks:
            if idurl not in chunks_by_page:
                chunks_by_page[idurl] = []
            chunks_by_page[idurl].append(order)

        # Iterate to group relevant chunks by page and get neighboring content
        for page_id in context_ids:
            if page_id in chunks_by_page:
                source_ids.append(page_id)
                page_summary = page_summary_map.get(page_id, "No summary.")

                # Get the order numbers of relevant chunks for this page
                relevant_orders = chunks_by_page[page_id]

                # Expand to include neighbors and remove duplicates
                orders_with_neighbors = set()
                for order_num in relevant_orders:
                    orders_with_neighbors.add(order_num - 1)
                    orders_with_neighbors.add(order_num)
                    orders_with_neighbors.add(order_num + 1)

                # Fetch all unique chunks (originals + neighbors) in correct document order
                expanded_chunk_rows = execute_query(conn, """
                    SELECT Content FROM TBLContent
                    WHERE idurl = %s AND "order" = ANY(%s)
                    ORDER BY "order" ASC;
                """, params=(page_id, list(orders_with_neighbors)), fetch=True)

                if expanded_chunk_rows:
                    detailed_context = "\n\n".join([row[0] for row in expanded_chunk_rows])
                    page_context = f"Page Summary:\n{page_summary}\n\nDetailed Information from this page:\n{detailed_context}"
                    final_context_list.append(page_context)

    if not final_context_list:
        return {
            "answer": "Could not build a context to answer the question.",
            "sources": [],
            "links": []
        }

    # 4. Build the prompt and get the final answer
    rag_prompt = build_rag_prompt(question, final_context_list)
    final_answer = get_rag_answer(rag_prompt)

    # 5. Get the breadcrumbs (sources) and URL trails (links) for the sources
    # source_breadcrumbs = [breadcrumb for url_id in set(source_ids) if (breadcrumb := get_breadcrumb(conn, url_id))]

    source_breadcrumbs = []
    source_links = []
    seen = set()

    for url_id in source_ids:
        if url_id not in seen:
            seen.add(url_id)
            if breadcrumb := get_breadcrumb(conn, url_id):
                source_breadcrumbs.append(breadcrumb)
                url_trail = get_url_trail(conn, url_id)
                source_links.append(url_trail or "")
    
    return {
        "answer": final_answer,
        "sources": source_breadcrumbs,
        "links": source_links
    }
