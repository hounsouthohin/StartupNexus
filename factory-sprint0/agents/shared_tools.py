import os
import subprocess
from datetime import datetime
from functools import lru_cache

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# --- Global Configurations & Clients (Singleton Pattern) ---
# For performance, clients are initialized once and reused across all tool calls.
try:
    qdrant_client = QdrantClient(url="http://qdrant:6333", timeout=60)
    openai_embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = QdrantVectorStore(client=qdrant_client, collection_name="factory_standards", embedding=openai_embeddings)
except Exception as e:
    # If clients fail to initialize, set them to None to prevent application crash.
    # Tools that depend on them will fail gracefully.
    qdrant_client = None
    openai_embeddings = None
    vectorstore = None
    print(f"[ERROR] Failed to initialize global clients: {e}")

# Setup basic logger (can be replaced with a more robust logger)
class Logger:
    def info(self, message):
        print(f"[INFO] {message}")
    def warning(self, message):
        print(f"[WARNING] {message}")
    def error(self, message):
        print(f"[ERROR] {message}")
logger = Logger()

# --- Tool Definitions ---

@tool
@lru_cache(maxsize=50)
def rag_search(query: str) -> str:
    """
    Searches for development standards in the 'factory_standards' Qdrant collection.
    Uses a global, cached client for high performance and reliability.
    Example: rag_search("How to implement Clerk authentication?")
    """
    logger.info(f"Executing rag_search with query: '{query}'")
    if not vectorstore:
        logger.error("RAG search failed: Vectorstore is not initialized.")
        return "Aucun résultat (erreur de recherche)."
    
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        docs = retriever.invoke(query)
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        logger.error(f"RAG search encountered an error: {e}")
        return "Aucun résultat (erreur de recherche)."

class WriteFileArgs(BaseModel):
    path: str = Field(description="The relative project path for the file. E.g., 'src/components/Button.tsx'. Absolute paths are not allowed.")
    content: str = Field(description="The complete and final content to be written to the file.")

@tool(args_schema=WriteFileArgs)
def write_file(path: str, content: str) -> str:
    """
    Writes content to a file at a specified relative path. Overwrites existing files.
    For security, absolute paths are prohibited.
    """
    # Security check: prevent writing outside the project directory.
    if os.path.isabs(path):
        return "Error: Absolute paths are forbidden for security reasons."

    try:
        # Log if the file already exists to track overwrites.
        if os.path.exists(path):
            logger.warning(f"File '{path}' already exists and will be overwritten.")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding='utf-8') as f:
            f.write(content)
        return f"File '{path}' was written successfully."
    except Exception as e:
        return f"Error writing file '{path}': {e}"

class ValidateSyntaxArgs(BaseModel):
    file_path: str = Field(description="The relative path of the file to validate. Supported extensions: .js, .ts, .tsx, .prisma.")

@tool(args_schema=ValidateSyntaxArgs)
def validate_syntax(file_path: str) -> str:
    """
    Validates the syntax of a file using external tools (ESLint for JS/TS, Prisma for schema).
    It relies on a central .eslintrc.json file for robust validation rules.
    Includes a 30-second timeout to prevent indefinite hangs.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    # Assumes the command is run from the root of the 'factory-sprint0' project
    # where the .eslintrc.json file is located.
    working_dir = '.' 

    try:
        if file_path.endswith((".js", ".ts", ".tsx")):
            # This command now relies on the .eslintrc.json file in the working directory
            command = ['npx', 'eslint', file_path]
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=30,
                cwd=working_dir
            )
            return f"ESLint validation for {file_path} successful."
        
        elif file_path.endswith(".prisma"):
            command = ['npx', 'prisma', 'validate', '--schema', file_path]
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=30,
                cwd=working_dir
            )
            return f"Prisma validation for {file_path} successful."
            
        else:
            return f"Validation not supported for file type: {file_path}. Skipping."
            
    except subprocess.TimeoutExpired:
        return f"Validation timed out for '{file_path}' after 30 seconds."
    except subprocess.CalledProcessError as e:
        # ESLint returns exit code 1 for linting errors, which is a "failure" for check=True
        # We need to return the output so the ReAct agent can fix it.
        return (f"Validation error for '{file_path}' (Exit Code: {e.returncode}):\n"
                f"STDOUT:\n{e.stdout}\n"
                f"STDERR:\n{e.stderr}")
    except FileNotFoundError:
        return "Error: 'npx' not found. Please ensure Node.js and npm are installed."
    except Exception as e:
        return f"An unexpected error occurred during validation of '{file_path}': {e}"

class PrismaMigrateArgs(BaseModel):
    schema_path: str = Field(description="The relative path to the 'schema.prisma' file.")

@tool(args_schema=PrismaMigrateArgs)
def prisma_migrate(schema_path: str) -> str:
    """
    Executes a Prisma migration conditionally. It first checks the migration status.
    If the database is out of sync or does not exist, it runs 'migrate dev'.
    Otherwise, it skips the migration. Includes a 60-second timeout.
    """
    if not os.path.exists(schema_path):
        return f"Error: Schema file not found at '{schema_path}'"

    schema_dir = os.path.dirname(schema_path) or '.'

    try:
        # Step 1: Check current migration status without check=True to handle failures gracefully.
        logger.info(f"Checking Prisma migration status for '{schema_path}'...")
        status_command = ['npx', 'prisma', 'migrate', 'status', '--schema', schema_path]
        status_result = subprocess.run(
            status_command, 
            capture_output=True, 
            text=True, 
            cwd=schema_dir, 
            timeout=60
        )

        # Step 2: Decide if migration is needed.
        # Run migration if status command failed (e.g., DB not found) or if schema is out of sync.
        run_migration = False
        if status_result.returncode != 0:
            logger.warning(f"Prisma migrate status failed (Exit Code: {status_result.returncode}). A migration is likely needed.\nSTDERR: {status_result.stderr}")
            run_migration = True
        elif "Database schema is not in sync" in status_result.stdout or "migrations to apply" in status_result.stdout:
            logger.info("Database schema is out of sync. A migration is needed.")
            run_migration = True
        else:
            logger.info("Prisma migration check: Database is up to date. No migration needed.")
            return f"Prisma migration check for '{schema_path}': Database is up to date."

        if run_migration:
            # Step 3: Generate a unique migration name and run the migration.
            logger.info("Executing prisma migrate dev...")
            migration_name = 'init_' + datetime.now().strftime("%Y%m%d_%H%M%S")
            migrate_command = ['npx', 'prisma', 'migrate', 'dev', '--name', migration_name, '--schema', schema_path]
            
            # Using check=True here because failure at this stage is a genuine error for the agent.
            result = subprocess.run(
                migrate_command, 
                capture_output=True, 
                text=True, 
                check=True, 
                cwd=schema_dir, 
                timeout=60
            )
            return f"Prisma migration '{migration_name}' for '{schema_path}' successful:\n{result.stdout}"
        
        # This part should not be reached due to the logic above, but as a safeguard:
        return "Prisma migration check completed with no action taken."

    except subprocess.TimeoutExpired:
        return f"Prisma migration timed out for '{schema_path}' after 60 seconds."
    except subprocess.CalledProcessError as e:
        return (f"Error during Prisma migration for '{schema_path}' (Exit Code: {e.returncode}):\n"
                f"STDOUT:\n{e.stdout}\n"
                f"STDERR:\n{e.stderr}")
    except FileNotFoundError:
        return "Error: 'npx' or 'prisma' not found. Please ensure Node.js and npm are installed."
    except Exception as e:
        return f"An unexpected error occurred during Prisma migration: {e}"
