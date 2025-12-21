import os
import subprocess
import e2b

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# --- Tool: write_file ---
class WriteFileArgs(BaseModel):
    path: str = Field(description="The full, relative path where the file should be written. E.g., 'src/components/Button.tsx'.")
    content: str = Field(description="The complete and final content to be written to the file.")

@tool(args_schema=WriteFileArgs)
def write_file(path: str, content: str) -> str:
    """
    Writes the provided 'content' to a file at the specified 'path'.
    This tool creates the file if it doesn't exist and overwrites it if it does.
    It's essential for creating the project structure and code files.
    """
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding='utf-8') as f:
            f.write(content)
        return f"File '{path}' was written successfully. Content snippet: {content[:100]}..."
    except Exception as e:
        return f"Error writing file '{path}': {e}"

# --- Tool: validate_syntax ---
class ValidateSyntaxArgs(BaseModel):
    file_path: str = Field(description="The relative path of the file to be validated. E.g., 'app/page.tsx'.")

@tool(args_schema=ValidateSyntaxArgs)
def validate_syntax(file_path: str) -> str:
    """
    Validates the syntax of a file based on its extension. It's a crucial tool
    for ensuring the generated code is correct before proceeding.
    - For .tsx files, it uses ESLint.
    - For .prisma files, it uses 'prisma validate'.
    Requires 'npx' to be available in the environment.
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found."
            
        if file_path.endswith(".tsx"):
            result = subprocess.run(
                ['npx', 'eslint', '--no-eslintrc', '--parser', '@typescript-eslint/parser', '--parser-options', '{"ecmaVersion": 2020, "sourceType": "module"}', '--rule', '{"semi": ["error", "always"]}', file_path],
                capture_output=True, text=True, check=True
            )
            return f"ESLint validation for {file_path} successful:\n{result.stdout}"
        elif file_path.endswith(".prisma"):
            result = subprocess.run(
                ['npx', 'prisma', 'validate', '--schema', file_path],
                capture_output=True, text=True, check=True
            )
            return f"Prisma validation for {file_path} successful:\n{result.stdout}"
        else:
            return f"Validation not supported for file type: {file_path}. Skipping."
    except subprocess.CalledProcessError as e:
        return f"Validation error for '{file_path}':\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
    except FileNotFoundError:
        return "Error: 'npx' not found. Please ensure Node.js and npm are installed and in the system's PATH."
    except Exception as e:
        return f"An unexpected error occurred during validation of '{file_path}': {e}"

# --- Tool: prisma_migrate ---
class PrismaMigrateArgs(BaseModel):
    schema_path: str = Field(description="The relative path to the 'schema.prisma' file.")

@tool(args_schema=PrismaMigrateArgs)
def prisma_migrate(schema_path: str) -> str:
    """
    Executes a Prisma migration using 'prisma migrate dev'. This tool is essential
    for applying schema changes to the database. It requires 'npx' and 'prisma'
    to be available in the environment. The '--name' of the migration is
    automatically set to 'init'.
    """
    if not os.path.exists(schema_path):
        return f"Error: Schema file not found at '{schema_path}'"

    schema_dir = os.path.dirname(schema_path) or '.'
    
    try:
        # Prisma needs to be run from the directory containing the schema file
        # or have it specified, but changing cwd is more robust for related tooling.
        result = subprocess.run(
            ['npx', 'prisma', 'migrate', 'dev', '--name', 'init', '--schema', schema_path],
            capture_output=True, text=True, check=True, cwd=schema_dir
        )
        return f"Prisma migration for '{schema_path}' successful:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Error during Prisma migration for '{schema_path}':\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
    except FileNotFoundError:
        return "Error: 'npx' or 'prisma' not found. Please ensure Node.js and npm are installed and Prisma is in node_modules."
    except Exception as e:
        return f"An unexpected error occurred during Prisma migration: {e}"
