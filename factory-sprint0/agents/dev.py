import os
import logging
import shutil
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

# Import des shared tools
from .shared_tools import (
    write_file,
    validate_syntax,
    prisma_migrate,
    rag_search,
    read_files,
    run_build,
)

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# --- Dev Agent v3 Ultimate – Version 3.1.2 Finale (Truncation Simple & Efficace) ---
def dev_agent(spec: str, mermaid: str, project_name: str = "default-project") -> dict:
    """
    Dev Agent v3 Ultimate – Stabilité maximale, exécution manuelle des tools,
    truncation simple évitant les ToolMessage orphelins.
    """
    # LLM principal
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    # Tools disponibles
    tools = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tool_map = {tool.name: tool for tool in tools}

    MAX_ITERATIONS = 20
    MAX_BUILD_ATTEMPTS = 6
    MAX_SPEC_TOKENS = 50000
    MAX_MERMAID_TOKENS = 10000

    # --- Helper summarization ---
    def summarize_text(text: str, max_tokens: int, description: str) -> str:
        try:
            current_tokens = llm.get_num_tokens(text)
        except Exception:
            current_tokens = len(text) // 4
        if current_tokens <= max_tokens:
            logger.info(f"{description} dans la limite ({current_tokens} tokens).")
            return text
        logger.warning(f"{description} trop long ({current_tokens} tokens) → summarization.")
        try:
            summary_prompt = [
                SystemMessage(content=f"Résume ce texte en moins de {max_tokens} tokens. Garde uniquement l’essentiel pour le développement logiciel."),
                HumanMessage(content=text)
            ]
            summary = llm.invoke(summary_prompt).content
            logger.info(f"{description} résumé à {llm.get_num_tokens(summary)} tokens.")
            return summary
        except Exception as e:
            logger.error(f"Summarization échouée : {e} → truncation brute.")
            return text[:int(max_tokens * 3.5)] + "\n\n[TRUNCATED]"

    # Summarization initiale
    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    # Messages initiaux
    messages = [
        SystemMessage(content="""
Tu es Dev Agent. Génère un code base Next.js 14+ App Router en suivant ce workflow séquentiel :

**Workflow :**

- **Étape 1 : `package.json`**
  - Génère le `package.json`. Le `package.json` DOIT inclure les scripts suivants: "build": "next build", "dev": "next dev", "start": "next start", "lint": "next lint", et "test": "jest".
  - Inclure aussi un jest.config.js avec la config standard.
  - **Consulte TOUJOURS le RAG (`rag_search`) pour obtenir les versions exactes des dépendances pinnées**.

- **Étape 2 : `schema.prisma`**
  - Génère le `schema.prisma`. Authentification déléguée à Clerk.

- **Étape 3 : Auth et Middleware**
  - Implémente Clerk dans `app/layout.tsx` et crée `middleware.ts`.

- **Étape 4 : Pages et Composants**
  - Utilise shadcn/ui + Zod pour validation.

- **Étape 5 : Validation Continue**
  - Après chaque `write_file` → `validate_syntax`.
  - Après `schema.prisma` → `prisma_migrate`.

- **Condition d'arrêt :**
  - Termine uniquement quand `run_build` réussit.

**Règles Générales :**
- Un fichier à la fois.
- Tout vient du RAG.
- Corrige en une itération si possible.
- Clerk uniquement. Interdit : bcrypt, JWT custom, champ password.
"""),
        HumanMessage(content=(
            f"Nom du projet : {project_name}\n\n"
            f"Specification architecturale :\n{summarized_spec}\n\n"
            f"Diagramme Mermaid :\n{summarized_mermaid}\n\n"
            "Commence immédiatement par l'Étape 1 : appelle rag_search pour les versions, puis génère package.json."
        ))
    ]

    files = {}
    final_message = ""
    build_attempts = 0
    build_success = False
    total_tokens_estimate = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.info(f"[DEV AGENT v3 ULTIMATE] Itération {iteration}/{MAX_ITERATIONS} | Build attempts: {build_attempts}")

        # === TRUNCATION SIMPLE & EFFICACE (évite ToolMessage orphelins) ===
        if len(messages) > 30:
            logger.warning("Historique trop long → truncation simple : garde début + derniers 20 messages")
            # Trouve l'index du premier ToolMessage
            first_tool_index = next((i for i, m in enumerate(messages) if isinstance(m, ToolMessage)), len(messages))
            # Garde tout jusqu'au premier tool + les 20 derniers messages
            messages = messages[:first_tool_index] + messages[-20:]

        # Appel LLM
        response = llm.bind_tools(tools).invoke(messages)
        messages.append(response)

        # Exécution manuelle des tools
        tool_messages = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)

                if tool_to_call:
                    try:
                        logger.info(f"Executing tool: {tool_name} with args: {tool_call['args']}")
                        tool_output = tool_to_call.invoke(tool_call["args"])
                        tool_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        logger.error(error_msg)
                        tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))
                else:
                    error_msg = f"Tool '{tool_name}' not found."
                    logger.error(error_msg)
                    tool_messages.append(ToolMessage(content=error_msg, tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            # Mise à jour files
            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        files[path] = content
                        logger.info(f"Fichier généré : {path}")

        # Détection build
        if any("Build successful" in str(m.content) for m in tool_messages):
            build_success = True
            build_attempts = 0
        elif any("build" in str(m.content).lower() and ("error" in str(m.content).lower() or "failed" in str(m.content).lower()) for m in tool_messages):
            build_attempts += 1

        # Self-reflection (list directe)
        reflection_messages = [
            SystemMessage(content=(
                "Analyse l’état actuel du projet selon le workflow séquentiel.\n"
                f"Tentatives build échouées consécutives : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                "- Si run_build a réussi → réponds exactement 'TERMINÉ : CODE PRÊT'\n"
                "- Si plus de 5 échecs build → réponds exactement 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue le workflow étape par étape en corrigeant précisément les erreurs détectées."
            )),
            *messages[-18:]
        ]
        reflection = llm.invoke(reflection_messages).content.strip()
        messages.append(HumanMessage(content=reflection))
        final_message = reflection

        if "TERMINÉ : CODE PRÊT" in reflection.upper():
            logger.info("Dev Agent : Build réussi → terminaison.")
            build_success = True
            break
        if "ÉCHEC : ERREUR RÉCURRENTE BUILD" in reflection.upper() or build_attempts >= MAX_BUILD_ATTEMPTS:
            logger.warning("Dev Agent : Trop d'échecs build → arrêt.")
            final_message = "ÉCHEC : ERREUR RÉCURRENTE BUILD"
            break

    # Stats + nettoyage
    try:
        total_tokens_estimate = sum(llm.get_num_tokens(m.content) for m in messages if hasattr(m, "content") and isinstance(m.content, str))
    except:
        total_tokens_estimate = "indisponible"

    for folder in ["node_modules", ".next", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
            logger.info(f"Nettoyage : {folder} supprimé.")

    logger.info("Dev Agent v3 Ultimate terminé.")
    return {
        "files": files,
        "final_message": final_message,
        "iterations": iteration,
        "success": build_success,
        "build_attempts": build_attempts,
        "total_messages": len(messages),
        "token_estimate": total_tokens_estimate
    }