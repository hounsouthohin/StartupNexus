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


# --- Dev Agent v3 Ultimate – Version 3.2 Breakthrough (Premier SaaS imminent) ---
def dev_agent(spec: str, mermaid: str, project_name: str = "default-project") -> dict:
    """
    Dev Agent v3 Ultimate – Version finale stable.
    Correction boucle jest.config.js + détection run_build + progression forcée.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    tools = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tool_map = {tool.name: tool for tool in tools}

    MAX_ITERATIONS = 30  # Augmenté pour donner de la marge
    MAX_BUILD_ATTEMPTS = 8
    MAX_SPEC_TOKENS = 50000
    MAX_MERMAID_TOKENS = 10000

    def summarize_text(text: str, max_tokens: int, description: str) -> str:
        try:
            current_tokens = llm.get_num_tokens(text)
        except Exception:
            current_tokens = len(text) // 4
        if current_tokens <= max_tokens:
            return text
        try:
            summary = llm.invoke([
                SystemMessage(content=f"Résume en moins de {max_tokens} tokens pour le développement."),
                HumanMessage(content=text)
            ]).content
            return summary
        except:
            return text[:int(max_tokens * 3.5)] + "\n\n[TRUNCATED]"

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    messages = [
        SystemMessage(content="""
Tu es Dev Agent autonome. Tu suis STRICTEMENT cet ordre :

1. RAG → génère package.json en PREMIER (versions pinned, @clerk/nextjs obligatoire)
2. jest.config.js avec babel-jest + next/babel (standard 2026)
3. prisma/schema.prisma → prisma_migrate
4. app/layout.tsx avec ClerkProvider + middleware.ts
5. Pages/composants shadcn/ui + Zod validation
6. run_build dès que package.json, layout.tsx, middleware.ts, schema.prisma existent

RÈGLES ABSOLUES :
- Un seul fichier par itération max.
- Ne réécris JAMAIS un fichier existant.
- Clerk uniquement (@clerk/nextjs). Jamais bcrypt, JWT, password field.
- Termine uniquement sur "Build successful" → "TERMINÉ : CODE PRÊT"
"""),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            "Étape 1 : appelle rag_search pour versions Next.js/Clerk/Prisma, puis génère package.json (UNE SEULE FOIS)."
        ))
    ]

    files = {}
    final_message = ""
    build_attempts = 0
    build_success = False

    for iteration in range(1, MAX_ITERATIONS + 1):
        logger.info(f"[DEV AGENT v3.2] Itération {iteration}/{MAX_ITERATIONS} | Build attempts: {build_attempts}")

        # Truncation ultra-safe V3 – Chronologique garantie (build from newest, reverse)
        if len(messages) > 28:
            logger.warning("Historique trop long → truncation ultra-safe V3 chronologique.")
            retained = [messages[0], messages[1]]  # System + Premier Human

            recent = []  # Build newest to oldest
            i = len(messages) - 1
            pair_count = 0
            max_pairs = 12

            while i >= 2 and pair_count < max_pairs:
                current = messages[i]

                if isinstance(current, ToolMessage):
                    found = False
                    for j in range(i-1, max(i-20, 0), -1):
                        prev = messages[j]
                        if (hasattr(prev, "tool_calls") and prev.tool_calls and
                            any(tc.get("id") == current.tool_call_id for tc in prev.tool_calls if tc.get("id"))):
                            recent.append(current) # ToolMessage first when building newest to oldest
                            recent.append(prev)    # Then its AIMessage parent
                            pair_count += 1
                            found = True
                            i = j - 1
                            break
                    if not found:
                        i -= 1 # Orphaned ToolMessage, skip
                else:
                    recent.append(current)
                    i -= 1

            recent.reverse()  # Now oldest to newest
            messages = retained + recent
            logger.info(f"Historique truncaté à {len(messages)} messages (chronologique sécurisé).")

        response = llm.bind_tools(tools).invoke(messages)
        messages.append(response)

        tool_messages = []
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)
                if tool_to_call:
                    try:
                        logger.info(f"Exécution tool: {tool_name}")
                        output = tool_to_call.invoke(tool_call["args"])
                        tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
                    except Exception as e:
                        tool_messages.append(ToolMessage(content=f"ERREUR {tool_name}: {e}", tool_call_id=tool_call["id"]))
                else:
                    tool_messages.append(ToolMessage(content=f"Tool {tool_name} inconnu", tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None and path not in files:  # ÉVITE RÉÉCRITURE
                        files[path] = content
                        logger.info(f"Fichier généré : {path}")

        # Détection build succès/échec
        build_output = " ".join(str(m.content) for m in tool_messages)
        if "Build successful" in build_output:
            build_success = True
            build_attempts = 0
        elif "build" in build_output.lower() and ("error" in build_output.lower() or "failed" in build_output.lower()):
            build_attempts += 1

        # Forçage progression si fichiers clés présents
        key_files = ["package.json", "app/layout.tsx", "middleware.ts", "prisma/schema.prisma"]
        if all(any(k in p for p in files) for k in key_files) and not build_success:
            messages.append(HumanMessage(content="Fichiers clés présents. Appelle run_build maintenant pour valider le projet."))

        # Reflection renforcée – VERSION DÉFINITIVE FIXÉE (anti-400 + paires préservées)
        safe_reflection_history = []
        i = len(messages) - 1
        pair_count = 0
        max_pairs = 10

        while i >= 0 and pair_count < max_pairs:
            current = messages[i]
            
            if isinstance(current, ToolMessage):
                found_parent = False
                for j in range(i-1, max(i-10, 0), -1):
                    prev = messages[j]
                    if (hasattr(prev, "tool_calls") and prev.tool_calls and 
                        any(tc["id"] == current.tool_call_id for tc in prev.tool_calls if "id" in tc)):
                        safe_reflection_history.insert(0, prev)
                        safe_reflection_history.insert(1, current)
                        pair_count += 1
                        found_parent = True
                        i = j - 1
                        break
                if not found_parent:
                    i -= 1
            else:
                safe_reflection_history.insert(0, current)
                i -= 1

        safe_reflection_history = safe_reflection_history[:20]

        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Fichiers générés : {list(files.keys())}\n"
                f"Build attempts : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                "- Si 'Build successful' dans les logs → réponds 'TERMINÉ : CODE PRÊT'\n"
                "- Si trop d'échecs → 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue l'étape suivante sans réécrire les fichiers existants."
            )),
            *safe_reflection_history
        ]

        # FIX ABSOLU : bind_tools obligatoire sur reflection
        reflection_response = llm.bind_tools(tools).invoke(reflection_messages)
        reflection = reflection_response.content.strip()

        if hasattr(reflection_response, "tool_calls") and reflection_response.tool_calls:
            logger.warning("Reflection a généré des tool_calls inattendus → ignorés pour sécurité")
            # Do not append placeholder ToolMessages to the main 'messages' list.
            # This was the source of the persistent BadRequestError.

        messages.append(HumanMessage(content=reflection))
        final_message = reflection

        if "TERMINÉ : CODE PRÊT" in reflection.upper():
            logger.info("SUCCESS TOTAL : Premier SaaS généré !")
            build_success = True
            break
        if build_attempts >= MAX_BUILD_ATTEMPTS:
            final_message = "ÉCHEC : ERREUR RÉCURRENTE BUILD"
            break

    # Nettoyage
    for folder in ["node_modules", ".next", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)

    logger.info("Dev Agent v3.2 terminé.")
    return {
        "files": files,
        "final_message": final_message,
        "iterations": iteration,
        "success": build_success,
        "build_attempts": build_attempts,
        "total_messages": len(messages)
    }