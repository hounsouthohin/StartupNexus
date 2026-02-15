import codecs
import json
import os
import subprocess
from datetime import datetime
import time

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Import central configuration
from config.factory_config import (
    QDRANT_URL,
    QDRANT_COLLECTION_NAME,
    EMBEDDING_MODEL,
    DEFAULT_VECTOR_SEARCH_LIMIT,
    SUBPROCESS_TIMEOUT_SHORT,
    SUBPROCESS_TIMEOUT_MEDIUM,
    SUBPROCESS_TIMEOUT_LONG
)

# --- Global Configurations & Clients (Singleton Pattern) ---
try:
    qdrant_client = QdrantClient(url=QDRANT_URL, timeout=SUBPROCESS_TIMEOUT_MEDIUM)
    openai_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectorstore = QdrantVectorStore(
        client=qdrant_client, 
        collection_name=QDRANT_COLLECTION_NAME, 
        embedding=openai_embeddings
    )
except Exception as e:
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

MAX_TOOL_OUTPUT_CHARS = 1800
RAG_CACHE_MAX_SIZE = 50
_rag_cache: dict[str, str] = {}


def _truncate_output(output: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
    if len(output) <= max_chars:
        return output
    half = max_chars // 2
    return (
        output[:half]
        + f"\n...[output tronque: {len(output) - max_chars} chars]...\n"
        + output[-half:]
    )


def _resolve_safe_path(path: str, base_dir: str = ".") -> tuple[bool, str]:
    if os.path.isabs(path):
        return False, "Absolute paths are forbidden for security reasons."
    base_abs = os.path.abspath(base_dir)
    candidate_abs = os.path.abspath(os.path.join(base_dir, path))
    if os.path.commonpath([base_abs, candidate_abs]) != base_abs:
        return False, "Path traversal outside project directory is forbidden."
    return True, candidate_abs

@tool
def rag_search(query: str) -> str:
    """
    Searches for development standards in the 'factory_standards' Qdrant collection.
    Uses a global, cached client for high performance and reliability.
    Example: rag_search("How to implement Clerk authentication?")
    """
    logger.info(f"Executing rag_search with query: '{query}'")
    if query in _rag_cache:
        return _rag_cache[query]
    if not vectorstore:
        logger.error("RAG search failed: Vectorstore is not initialized.")
        return "Aucun résultat (erreur de recherche)."
    
    try:
        retriever = vectorstore.as_retriever(search_kwargs={"k": DEFAULT_VECTOR_SEARCH_LIMIT})
        docs = retriever.invoke(query)
        result = "\n\n".join([doc.page_content for doc in docs])
        if len(_rag_cache) >= RAG_CACHE_MAX_SIZE:
            _rag_cache.pop(next(iter(_rag_cache)))
        _rag_cache[query] = result
        return result
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
    is_safe, safe_path_or_err = _resolve_safe_path(path)
    if not is_safe:
        return f"Error: {safe_path_or_err}"

    try:
        safe_path = safe_path_or_err
        # Log if the file already exists to track overwrites.
        if os.path.exists(safe_path):
            logger.warning(f"File '{path}' already exists and will be overwritten.")
        
        parent_dir = os.path.dirname(safe_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(safe_path, "w", encoding='utf-8') as f:
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
    Includes a timeout to prevent indefinite hangs.
    """
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    working_dir = '.' 

    try:
        if file_path.endswith((".js", ".ts", ".tsx")):
            command = ['npx', 'eslint', file_path]
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True, 
                timeout=SUBPROCESS_TIMEOUT_SHORT,
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
                timeout=SUBPROCESS_TIMEOUT_SHORT,
                cwd=working_dir
            )
            return f"Prisma validation for {file_path} successful."
            
        else:
            return f"Validation not supported for file type: {file_path}. Skipping."
            
    except subprocess.TimeoutExpired:
        return f"Validation timed out for '{file_path}' after {SUBPROCESS_TIMEOUT_SHORT} seconds."
    except subprocess.CalledProcessError as e:
        return _truncate_output(
            f"Validation error for '{file_path}' (Exit Code: {e.returncode}):\n"
            f"STDOUT:\n{e.stdout}\n"
            f"STDERR:\n{e.stderr}"
        )
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
    Includes a retry mechanism to handle filesystem sync delays.
    """
    # --- START MODIFICATION ---
    # Retry loop to wait for the file to be available
    max_retries = 5
    retry_delay = 0.5 # seconds
    for attempt in range(max_retries):
        if os.path.exists(schema_path):
            logger.info(f"Schema file found at '{schema_path}' on attempt {attempt + 1}.")
            break
        logger.warning(f"Schema file not found at '{schema_path}' on attempt {attempt + 1}. Retrying in {retry_delay}s...")
        time.sleep(retry_delay)
    else:
        # This 'else' belongs to the 'for' loop and runs if the loop completes without a 'break'
        logger.error(f"Schema file not found at '{schema_path}' after {max_retries} retries.")
        return f"Error: Schema file not found at '{schema_path}' after multiple retries."
    # --- END MODIFICATION ---

    schema_dir = os.path.dirname(schema_path) or '.'
    
    # ... (rest of the function remains the same)
    try:
        # Step 1: Check current migration status...
        logger.info(f"Checking Prisma migration status for '{schema_path}'...")
        status_command = ['npx', 'prisma', 'migrate', 'status', '--schema', schema_path]
        status_result = subprocess.run(
            status_command, 
            capture_output=True, 
            text=True, 
            cwd=schema_dir, 
            timeout=SUBPROCESS_TIMEOUT_MEDIUM
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
                timeout=SUBPROCESS_TIMEOUT_MEDIUM
            )
            return _truncate_output(
                f"Prisma migration '{migration_name}' for '{schema_path}' successful:\n{result.stdout}"
            )
        
        # This part should not be reached due to the logic above, but as a safeguard:
        return "Prisma migration check completed with no action taken."

    except subprocess.TimeoutExpired:
        return f"Prisma migration timed out for '{schema_path}' after {SUBPROCESS_TIMEOUT_MEDIUM} seconds."
    except subprocess.CalledProcessError as e:
        return _truncate_output(
            f"Error during Prisma migration for '{schema_path}' (Exit Code: {e.returncode}):\n"
            f"STDOUT:\n{e.stdout}\n"
            f"STDERR:\n{e.stderr}"
        )
    except FileNotFoundError:
        return "Error: 'npx' or 'prisma' not found. Please ensure Node.js and npm are installed."
    except Exception as e:
        return f"An unexpected error occurred during Prisma migration: {e}"

class ReadFileArgs(BaseModel):
    path: str = Field(description="The relative project path for the file to read. E.g., 'src/components/Button.tsx'.")

@tool(args_schema=ReadFileArgs)
def read_files(path: str) -> str:
    """
    Reads the content of a file at a specified relative path and returns it as a string.
    """
    is_safe, safe_path_or_err = _resolve_safe_path(path)
    if not is_safe:
        return f"Error: {safe_path_or_err}"
    safe_path = safe_path_or_err

    if not os.path.exists(safe_path):
        return f"Error: File not found at '{path}'"
    try:
        with open(safe_path, "r", encoding='utf-8') as f:
            content = f.read()
        return _truncate_output(content)
    except Exception as e:
        return f"Error reading file '{path}': {e}"

class RunBuildArgs(BaseModel):
    project_dir: str = Field(description="Répertoire racine du projet (défaut: '.')", default='.')

@tool(args_schema=RunBuildArgs)
def run_build(project_dir: str = '.') -> str:
    """
    Executes 'npm install' then 'npm run build' in the specified project directory to validate the build process.
    Returns a detailed error message if the build or install fails, for use in ReAct loops.
    """
    logger.info(f"Executing 'npm install' and 'npm run build' in directory '{project_dir}'...")

    package_json_path = os.path.join(project_dir, 'package.json')
    if not os.path.exists(package_json_path):
        return f"Error: package.json not found at '{package_json_path}'. Cannot run build."

    try:
        # Step 1: Run npm install
        logger.info(f"Running npm install in '{project_dir}'...")
        install_command = ['npm', 'install']
        subprocess.run(
            install_command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG # Use long timeout for npm install
        )
        logger.info("npm install completed successfully.")

        # Step 2: Run npm run build
        logger.info(f"Running npm run build in '{project_dir}'...")
        build_command = ['npm', 'run', 'build']
        result = subprocess.run(
            build_command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG
        )
        logger.info(f"Build successful in '{project_dir}'.")
        return _truncate_output(f"Build successful: {result.stdout}")
    except subprocess.TimeoutExpired as e:
        return f"Command timed out in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds: {e.cmd}"
    except subprocess.CalledProcessError as e:
        error_message = _truncate_output(
            f"Command failed (code {e.returncode}): {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )
        logger.error(error_message)
        return error_message
    except FileNotFoundError:
        return "Error: 'npm' not found. Please ensure Node.js and npm are installed and in the PATH."
    except Exception as e:
        return f"An unexpected error occurred during build process: {e}"
class RunTestsArgs(BaseModel):
    project_dir: str = Field(description="Répertoire racine du projet (défaut: '.')", default='.')
    files: dict = Field(description="A dictionary of files to write to disk before running tests, with path as key and content as value.")

@tool(args_schema=RunTestsArgs)
def run_tests(project_dir: str = '.', files: dict = None) -> str:
    """
    Writes a dictionary of files to disk, then executes 'npx jest --coverage' in the specified project directory.
    Installs dependencies using 'npm ci' or 'npm install' if a package.json is found.
    Returns a detailed error message if tests fail, for use in ReAct loops.
    """
    logger.info(f"Executing tests in directory '{project_dir}'...")

    if files:
        logger.info(f"Writing {len(files)} files to disk before running tests...")
        for path, content in files.items():
            try:
                # Ensure parent directories exist
                is_safe, safe_path_or_err = _resolve_safe_path(path, project_dir)
                if not is_safe:
                    return f"Error writing file '{path}': {safe_path_or_err}"
                safe_path = safe_path_or_err
                parent_dir = os.path.dirname(safe_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                
                content_to_write = content
                try:
                    # Decode escaped characters like \\n into \n for all files
                    content_to_write = codecs.decode(content, 'unicode_escape')
                except Exception as e:
                    # Log but don't fail if decoding fails for non-package.json files
                    logger.warning(f"Warning: Failed to decode unicode escape for '{path}'. Details: {e}. Original content: {content}")
                    # Fallback to original content if decoding fails
                    content_to_write = content

                # Sanitize package.json specifically
                if path == 'package.json':
                    logger.info("Sanitizing package.json before writing...")
                    # Explicitly replace the incorrect ts-jest version
                    content_to_write = content_to_write.replace('"ts-jest": "29.5.0"', '"ts-jest": "29.1.2"')
                    # Force "next" version to "14.2.3" to resolve peer dependency conflicts
                    content_to_write = content_to_write.replace(
                        '"next": "13.4.0"', '"next": "14.2.3"'
                    ).replace( # Also replace if it's "^13.x.x" or similar
                        '"next": "^13.4.0"', '"next": "14.2.3"'
                    ).replace( # Another common problematic version
                        '"next": "^14.0.0"', '"next": "14.2.3"'
                    ).replace( # Ensure any other major 13 or 14 is also updated if needed
                        '"next": "^13', '"next": "14.2.3"'
                    ).replace(
                        '"next": "14.0.0"', '"next": "14.2.3"'
                    ).replace(
                        '"next": "14.1.0"', '"next": "14.2.3"'
                    )

                with open(safe_path, "w", encoding='utf-8') as f:
                    f.write(content_to_write)
                logger.info(f"Successfully wrote file: {path}")
            except Exception as e:
                error_msg = f"Error writing file '{path}' at the start of run_tests: {e}"
                logger.error(error_msg)
                return error_msg
    
    # --- Ensure critical config files exist for testing ---
    # Grok's recommendation: Inject standard tsconfig.json and jest.setup.js if they don't exist.
    
    # tsconfig.json content
    tsconfig_content = """{
  "compilerOptions": {
    "target": "es2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "baseUrl": ".",
    "paths": { "@/*": ["./*"] }
  },
  "include": ["**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}"""
    tsconfig_path = os.path.join(project_dir, 'tsconfig.json')
    if not os.path.exists(tsconfig_path):
        logger.info(f"Writing default tsconfig.json to '{tsconfig_path}'...")
        try:
            with open(tsconfig_path, "w", encoding='utf-8') as f:
                f.write(tsconfig_content)
            logger.info(f"Successfully wrote file: {tsconfig_path}")
        except Exception as e:
            error_msg = f"Error writing default tsconfig.json: {e}"
            logger.error(error_msg)
            return error_msg

    # jest.setup.js content
    jest_setup_content = """import '@testing-library/jest-dom';"""
    jest_setup_path = os.path.join(project_dir, 'jest.setup.js')
    if not os.path.exists(jest_setup_path):
        logger.info(f"Writing default jest.setup.js to '{jest_setup_path}'...")
        try:
            with open(jest_setup_path, "w", encoding='utf-8') as f:
                f.write(jest_setup_content)
            logger.info(f"Successfully wrote file: {jest_setup_path}")
        except Exception as e:
            error_msg = f"Error writing default jest.setup.js: {e}"
            logger.error(error_msg)
            return error_msg

    # jest.config.js content
    jest_config_content = """module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    '^@clerk/nextjs/middleware$': '<rootDir>/__mocks__/clerk-middleware.js',
  },
};"""
    jest_config_path = os.path.join(project_dir, 'jest.config.js')
    if not os.path.exists(jest_config_path):
        logger.info(f"Writing default jest.config.js to '{jest_config_path}'...")
        try:
            with open(jest_config_path, "w", encoding='utf-8') as f:
                f.write(jest_config_content)
            logger.info(f"Successfully wrote file: {jest_config_path}")
        except Exception as e:
            error_msg = f"Error writing default jest.config.js: {e}"
            logger.error(error_msg)
            return error_msg
            
    # Clerk middleware mock content (updated per Grok's suggestion)
    clerk_middleware_mock_content = """module.exports = {
  withClerkMiddleware: (handler) => handler,
  clerkMiddleware: (handler) => handler, // Added per Grok's suggestion
};"""
    clerk_middleware_mock_path = os.path.join(project_dir, '__mocks__', 'clerk-middleware.js')
    os.makedirs(os.path.dirname(clerk_middleware_mock_path), exist_ok=True)
    if not os.path.exists(clerk_middleware_mock_path):
        logger.info(f"Writing clerk middleware mock to '{clerk_middleware_mock_path}'...")
        try:
            with open(clerk_middleware_mock_path, "w", encoding='utf-8') as f:
                f.write(clerk_middleware_mock_content)
            logger.info(f"Successfully wrote file: {clerk_middleware_mock_path}")
        except Exception as e:
            error_msg = f"Error writing clerk middleware mock: {e}"
            logger.error(error_msg)
            return error_msg
    
    package_json_path = os.path.join(project_dir, 'package.json')
    if os.path.exists(package_json_path):
        logger.info(f"package.json found in '{project_dir}'. Installing dev dependencies...")
        
        npm_command = []
        if os.path.exists(os.path.join(project_dir, 'package-lock.json')):
            logger.info(f"package-lock.json found. Using 'npm ci' for consistent installation.")
            npm_command = ['npm', 'ci']
        else:
            logger.info(f"package-lock.json not found. Using 'npm install --save-dev' for installation.")
            npm_command = [
                'npm', 'install', '--save-dev',
                'jest', '@testing-library/react', '@testing-library/jest-dom',
                'babel-jest', '@babel/preset-env', '@babel/preset-react',
                'ts-jest', 'typescript', 'zod', 'node-mocks-http',
                'identity-obj-proxy', 'jest-environment-jsdom'
            ]

        try:
            install_result = subprocess.run(
                npm_command,
                capture_output=True,
                text=True,
                check=True,
                cwd=project_dir,
                timeout=SUBPROCESS_TIMEOUT_LONG,
                env={"NODE_ENV": "development", **os.environ} if 'ci' in npm_command else os.environ
            )
            logger.info(
                _truncate_output(
                    f"npm command completed successfully. STDOUT:\n{install_result.stdout}\nSTDERR:\n{install_result.stderr}"
                )
            )

            # Explicitly check if jest executable is present after npm install
            jest_bin_path = os.path.join(project_dir, 'node_modules', '.bin', 'jest')
            if not os.path.exists(jest_bin_path):
                return _truncate_output(
                    f"Error: Jest executable not found at '{jest_bin_path}' after npm command. Installation might have failed or been incomplete. npm STDOUT:\n{install_result.stdout}\nnpm STDERR:\n{install_result.stderr}"
                )

        except subprocess.TimeoutExpired:
            return f"npm command timed out in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds."
        except subprocess.CalledProcessError as e:
            error_message = _truncate_output(
                f"npm command failed (code {e.returncode}): {e.cmd}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            )
            logger.error(error_message)
            return error_message
        except FileNotFoundError:
            return "Error: 'npm' not found during dependency installation. Please ensure Node.js and npm are installed and in the PATH."
        except Exception as e:
            return f"An unexpected error occurred during npm command: {e}"

    logger.info(f"Attempting to run Jest tests in '{project_dir}'...")
    try:
        command = ['npx', 'jest', '--coverage']
        logger.info(f"Executing Jest command: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=project_dir,
            timeout=SUBPROCESS_TIMEOUT_LONG # Using SUBPROCESS_TIMEOUT_LONG for 120s
        )
        logger.info(
            _truncate_output(
                f"Jest tests command completed. STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )
        )
        logger.info(f"Tests passed in '{project_dir}'.")
        return _truncate_output(f"Tests passed: {result.stdout}")
    except subprocess.TimeoutExpired:
        logger.error(f"Test run timed out for 'npx jest --coverage' in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds.")
        return f"Test run timed out for 'npx jest --coverage' in '{project_dir}' after {SUBPROCESS_TIMEOUT_LONG} seconds."
    except subprocess.CalledProcessError as e:
        error_message = _truncate_output(
            f"Tests failed (code {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        )
        logger.error(error_message)
        return error_message
    except FileNotFoundError:
        logger.error("Error: 'npx' not found during test execution. Please ensure Node.js and npm are installed and in the PATH.")
        return "Error: 'npx' not found during test execution. Please ensure Node.js and npm are installed and in the PATH."
    except Exception as e:
        logger.error(f"An unexpected error occurred during tests: {e}")
        return f"An unexpected error occurred during tests: {e}"


class LogToLearnerArgs(BaseModel):
    project_name: str = Field(description="Nom du projet (ex: demo-saas)")
    metric: str = Field(description="Nom de la metrique (ex: build_success)")
    value: str = Field(description="Valeur serialisee de la metrique")


@tool(args_schema=LogToLearnerArgs)
def log_to_learner(project_name: str, metric: str, value: str) -> str:
    """
    Appends a learner shadow metric to logs/shadow/learner_shadow_log.json.
    Safe no-op if the file is missing or malformed: it will be initialized.
    """
    log_path = os.path.join("logs", "shadow", "learner_shadow_log.json")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    payload = {
        "project_name": project_name,
        "metric": metric,
        "value": value,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    try:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
        else:
            data = {}

        if "events" not in data or not isinstance(data.get("events"), list):
            data["events"] = []
        data["events"].append(payload)
        data["total_suggestions"] = len(data["events"])

        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=True, indent=2)
        return f"Learner log updated: {metric} for {project_name}"
    except Exception as e:
        return f"Error updating learner log: {e}"
