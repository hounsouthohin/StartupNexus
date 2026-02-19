import os
import logging
import shutil
import re
import ast
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
from utils.prompt_loader import load_prompt

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

    MAX_ITERATIONS = 10
    MAX_BUILD_ATTEMPTS = 8
    # Budgets ramenés à des tailles réalistes pour limiter la pression TPM
    MAX_SPEC_TOKENS = 4000
    MAX_MERMAID_TOKENS = 1200
    MAX_TOOL_OUTPUT_CHARS = 1800
    MAX_MAIN_HISTORY_CHARS = 14000

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

    def _compact(text: str) -> str:
        """Compacte les espaces pour réduire la taille sans perdre l'information utile."""
        return re.sub(r"\s+", " ", text).strip()

    def _shrink_tool_output(tool_name: str, output: str, max_chars: int = MAX_TOOL_OUTPUT_CHARS) -> str:
        """
        Réduit les sorties tools avant insertion dans l'historique du LLM.
        Conserve début+fin, là où les erreurs importantes apparaissent souvent.
        """
        compact = _compact(output)
        if len(compact) <= max_chars:
            return compact
        head = max_chars // 2
        tail = max_chars - head
        return (
            f"[{tool_name}] OUTPUT_TRUNCATED total_chars={len(compact)} | "
            f"head: {compact[:head]} ... tail: {compact[-tail:]}"
        )

    def _main_context(messages_list):
        """
        Construit le contexte sous budget en conservant l'intégrité des couples
        AI(tool_calls) + ToolMessage(s). Évite l'erreur OpenAI 400 sur tool_call_id.
        """
        if len(messages_list) <= 2:
            return messages_list

        kept = [messages_list[0], messages_list[1]]
        current_chars = sum(len(str(getattr(m, "content", ""))) for m in kept)

        # Découpe en "turns" cohérents après les 2 messages initiaux.
        turns = []
        i = 2
        n = len(messages_list)
        while i < n:
            msg = messages_list[i]
            has_tool_calls = hasattr(msg, "tool_calls") and bool(getattr(msg, "tool_calls", None))

            if has_tool_calls:
                turn = [msg]
                i += 1
                while i < n and isinstance(messages_list[i], ToolMessage):
                    turn.append(messages_list[i])
                    i += 1

                expected_ids = {tc.get("id") for tc in msg.tool_calls if tc.get("id")}
                got_ids = {tm.tool_call_id for tm in turn[1:] if getattr(tm, "tool_call_id", None)}

                # Ne garder que les turns complets (assistant + toutes réponses tools).
                if expected_ids and expected_ids.issubset(got_ids):
                    turns.append(turn)
                else:
                    logger.warning("Turn incomplet tool_calls ignoré dans _main_context")
            else:
                turns.append([msg])
                i += 1

        selected = []
        for turn in reversed(turns):
            turn_chars = sum(len(str(getattr(m, "content", ""))) for m in turn)
            if current_chars + turn_chars > MAX_MAIN_HISTORY_CHARS:
                break
            selected.append(turn)
            current_chars += turn_chars

        selected.reverse()
        flattened = [m for turn in selected for m in turn]
        return kept + flattened

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    prompt = load_prompt("dev")
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            "Étape 1 OBLIGATOIRE : appelle rag_search('versions exactes next.js clerk prisma tailwind shadcn zod') puis génère package.json."
        ))
    ]

    files = {}
    final_message = ""
    build_attempts = 0
    build_attempted = False
    build_success = False
    last_build_error = ""
    last_test_error = ""
    last_failed_command = ""

    def _extract_stderr(output: str) -> str:
        if not output:
            return ""
        marker = "STDERR:\n"
        if marker in output:
            return output.split(marker, 1)[1].strip()
        return ""

    def _extract_failed_command(output: str) -> str:
        match = re.search(r"Command failed \(code \d+\):\s*(\[[^\]]+\])", output)
        if not match:
            return ""
        raw_cmd = match.group(1)
        try:
            parsed = ast.literal_eval(raw_cmd)
            if isinstance(parsed, list):
                return " ".join(str(x) for x in parsed)
        except Exception:
            pass
        return raw_cmd

    stagnant_iterations = 0
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

        main_messages = _main_context(messages)
        response = llm.bind_tools(tools).invoke(main_messages)
        messages.append(response)

        tool_messages = []
        raw_tool_outputs = []
        wrote_file_this_iter = False
        called_build_this_iter = False
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)
                if tool_to_call:
                    try:
                        logger.info(f"Exécution tool: {tool_name}")
                        output = tool_to_call.invoke(tool_call["args"])
                        raw_output = str(output)
                        raw_tool_outputs.append(raw_output)

                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            if "Build successful" in raw_output:
                                last_build_error = ""
                                last_failed_command = ""
                            else:
                                extracted_stderr = _extract_stderr(raw_output)
                                last_build_error = extracted_stderr[:2000] if extracted_stderr else raw_output[:2000]
                                failed_cmd = _extract_failed_command(raw_output)
                                if failed_cmd:
                                    last_failed_command = failed_cmd

                        if tool_name == "run_tests":
                            if "Tests passed" in raw_output:
                                last_test_error = ""
                            else:
                                extracted_stderr = _extract_stderr(raw_output)
                                last_test_error = extracted_stderr[:2000] if extracted_stderr else raw_output[:2000]

                        shrunk_output = _shrink_tool_output(tool_name, raw_output)
                        tool_messages.append(ToolMessage(content=shrunk_output, tool_call_id=tool_call["id"]))
                    except Exception as e:
                        error_text = f"ERREUR {tool_name}: {e}"
                        raw_tool_outputs.append(error_text)
                        if tool_name == "run_build":
                            last_build_error = error_text[:2000]
                            last_failed_command = "run_build"
                        if tool_name == "run_tests":
                            last_test_error = error_text[:2000]
                        tool_messages.append(ToolMessage(content=error_text, tool_call_id=tool_call["id"]))
                else:
                    tool_messages.append(ToolMessage(content=f"Tool {tool_name} inconnu", tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None and path not in files:  # ÉVITE RÉÉCRITURE
                        files[path] = content
                        wrote_file_this_iter = True
                        logger.info(f"Fichier généré : {path}")

        # Détection build succès/échec
        build_output = " ".join(raw_tool_outputs)
        if "Build successful" in build_output:
            build_success = True
            build_attempts = 0
        elif "build" in build_output.lower() and ("error" in build_output.lower() or "failed" in build_output.lower()):
            build_attempts += 1

        if wrote_file_this_iter or called_build_this_iter:
            stagnant_iterations = 0
        else:
            stagnant_iterations += 1

        # Forçage progression si fichiers clés présents
        key_files = ["package.json", "app/layout.tsx", "middleware.ts", "prisma/schema.prisma"]
        if all(any(k in p for p in files) for k in key_files) and not build_success:
            messages.append(HumanMessage(content="Fichiers clés présents. Appelle run_build maintenant pour valider le projet."))

        # Garde-fou: si le modele stagne sans progres, forcer un run_build.
        if not build_success and not called_build_this_iter and (stagnant_iterations >= 2 or iteration >= MAX_ITERATIONS - 1):
            forced_build_output = str(run_build.invoke({"project_dir": "."}))
            build_attempted = True
            called_build_this_iter = True
            raw_tool_outputs.append(forced_build_output)
            messages.append(HumanMessage(content=f"[FORCED_RUN_BUILD]\n{_shrink_tool_output('run_build', forced_build_output)}"))
            if "Build successful" in forced_build_output:
                build_success = True
                build_attempts = 0
                last_build_error = ""
                last_failed_command = ""
            else:
                build_attempts += 1
                extracted_stderr = _extract_stderr(forced_build_output)
                last_build_error = extracted_stderr[:2000] if extracted_stderr else forced_build_output[:2000]
                failed_cmd = _extract_failed_command(forced_build_output)
                if failed_cmd:
                    last_failed_command = failed_cmd

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

        # REMPLACE tout le bloc "Reflection renforcée" par ceci :
        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Fichiers générés : {list(files.keys())}\n"
                f"Build attempts : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                "- Si 'Build successful' dans les logs → réponds 'TERMINÉ : CODE PRÊT'\n"
                "- Si trop d'échecs → 'ÉCHEC : ERREUR RÉCURRENTE BUILD'\n"
                "- Sinon → continue l'étape suivante sans réécrire les fichiers existants."
            )),
            HumanMessage(content=f"Fichiers générés jusqu'ici : {list(files.keys())}")
        ]

        # PAS de bind_tools sur la reflection — juste du texte
        reflection_response = llm.invoke(reflection_messages)
        reflection = reflection_response.content.strip()
    # Pas besoin de gérer tool_calls ici — llm.invoke sans tools ne peut pas en générer

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

    if not build_attempted and not build_success:
        final_message = "BuildNotAttempted: run_build n'a pas ete execute."
    logger.info("Dev Agent v3.2 terminé.")
    return {
        "files": files,
        "final_message": final_message,
        "success": build_success,
        "metadata": {
            "iterations": iteration,
            "build_attempts": build_attempts,
            "build_attempted": build_attempted,
            "total_files": len(files),
            "last_build_error": last_build_error[:2000] if last_build_error else "",
            "last_test_error": last_test_error[:2000] if last_test_error else "",
            "last_failed_command": last_failed_command,
        },
    }
