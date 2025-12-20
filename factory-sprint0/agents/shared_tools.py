import os
import subprocess
import e2b

def write_file(path: str, content: str) -> str:
    """Writes content to a specified file path."""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Fichier '{path}' écrit avec succès."
    except Exception as e:
        return f"Erreur lors de l'écriture du fichier '{path}': {e}"

def validate_syntax(file_path: str) -> str:
    """
    Validates the syntax of a file based on its extension.
    Supports .tsx (ESLint) and .prisma (Prisma Validate).
    """
    try:
        if file_path.endswith(".tsx"):
            # Assuming npx is available in the environment where this runs
            result = subprocess.run(
                ['npx', 'eslint', '--no-eslintrc', '--parser', '@typescript-eslint/parser', '--parser-options', '{"ecmaVersion": 2020, "sourceType": "module"}', '--rule', '{"semi": ["error", "always"]}', file_path],
                capture_output=True, text=True, check=True
            )
            return f"ESLint validation for {file_path}:\n{result.stdout}\n{result.stderr}"
        elif file_path.endswith(".prisma"):
            result = subprocess.run(
                ['npx', 'prisma', 'validate', '--schema', file_path],
                capture_output=True, text=True, check=True
            )
            return f"Prisma validation for {file_path}:\n{result.stdout}\n{result.stderr}"
        else:
            return f"Validation non supportée pour le type de fichier : {file_path}"
    except subprocess.CalledProcessError as e:
        return f"Erreur de validation pour '{file_path}':\n{e.stderr}"
    except FileNotFoundError:
        return f"Erreur: 'npx' ou le linter/validator requis n'a pas été trouvé. Assurez-vous que Node.js/npm et les outils sont installés."
    except Exception as e:
        return f"Une erreur inattendue est survenue lors de la validation de '{file_path}': {e}"

def prisma_migrate(schema_path: str) -> str:
    """
    Executes a Prisma migration. Assumes the current working directory
    or a specified temporary directory context where `npx prisma` can be run.
    """
    schema_dir = os.path.dirname(schema_path) if os.path.dirname(schema_path) else '.'
    
    try:
        original_cwd = os.getcwd()
        os.chdir(schema_dir)
        
        result = subprocess.run(
            ['npx', 'prisma', 'migrate', 'dev', '--name', 'init', '--schema', os.path.basename(schema_path)],
            capture_output=True, text=True, check=True
        )
        
        os.chdir(original_cwd) # Change back
        return f"Prisma migration for '{schema_path}':\n{result.stdout}\n{result.stderr}"
    except subprocess.CalledProcessError as e:
        os.chdir(original_cwd) # Ensure we change back even on error
        return f"Erreur lors de la migration Prisma pour '{schema_path}':\n{e.stderr}\n{e.stdout}"
    except FileNotFoundError:
        os.chdir(original_cwd) # Ensure we change back even on error
        return f"Erreur: 'npx' ou 'prisma' n'a pas été trouvé. Assurez-vous que Node.js/npm et Prisma sont installés."
    except Exception as e:
        os.chdir(original_cwd) # Ensure we change back even on error
        return f"Une erreur inattendue est survenue lors de la migration Prisma pour '{file_path}': {e}"
