# CIROH AI Bot - Database Population Engine

This repository contains the Jupyter Notebook and necessary files to set up and populate the PostgreSQL database for the CIROH AI Bot project. The main script (`PopulateDB.ipynb`) performs the following actions:
1.  Scrapes the site structure from `docs.ciroh.org`.
2.  Populates a hierarchical URL table in a PostgreSQL database.
3.  For each URL with corresponding markdown content, it calls the OpenAI API to generate a structured summary (including keywords and entities).
4.  Generates vector embeddings for each summary and stores them in the database.

---

## Prerequisites

Before you begin, ensure you have the following installed:
* **Python 3.9+** (or a working Anaconda environment)
* **PostgreSQL** with the **`pgvector`** extension enabled.
* Access to the **OpenAI API** with a valid API key.
* A local clone of the `CIROH-scraper` repository containing the markdown files.

---

## ⚙️ Installation & Setup

Follow these steps to get your local environment set up and ready to run the notebook.

### 1. Clone the Repository

Clone this repository to your local machine:
```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. Install Dependencies

Install all the required Python libraries using the provided `requirements.txt` file. If you are using Anaconda, you can install them via `pip` within your conda environment.
```bash
pip install -r requirements.txt
```

### 3. Configure the Database

This project includes a `schema.sql` file to create the necessary database structure.

1.  Create a new database in PostgreSQL.
2.  Connect to your new database using a tool like `psql` or a GUI client.
3.  Execute the `schema.sql` script to create all the tables and indexes.

    **Example using `psql`:**
    ```bash
    psql -U your_postgres_user -d your_database_name -f schema.sql
    ```

### 4. Set Up Environment Variables

The script uses a `.env` file to manage sensitive information and configuration.

1.  Create a file named `.env` in the root directory of the project.
2.  Add the following variables to the `.env` file, replacing the placeholder values with your actual credentials and settings:

    ```env
    # PostgreSQL Connection Details
    POSTGRES_HOST=localhost
    POSTGRES_DB=your_database_name
    POSTGRES_USER=your_postgres_user
    POSTGRES_PASSWORD=your_postgres_password

    # OpenAI API Details
    OPENAI_API_KEY=sk-your-openai-api-key
    EMBEDDING_MODEL=text-embedding-3-large
    ```

---

## ▶️ Running the Notebook

Once the setup is complete, you can run the data population process.

1.  Ensure your Anaconda environment is activated.
2.  Start the Jupyter Notebook server:
    ```bash
    jupyter notebook
    ```
3.  Open the `PopulateDB.ipynb` file in your browser.
4.  Run the cells sequentially from top to bottom. The notebook will connect to the database, scrape the site, generate summaries and embeddings, and populate the `tblurls` table.

The process may take some time depending on the number of pages to process and the latency of the OpenAI API.
