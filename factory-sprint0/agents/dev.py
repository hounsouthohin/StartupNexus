import os
import json
import logging
import shutil
import re
import ast
from datetime import datetime, timezone
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
    get_stack_id,
)
from .stack_config import get_blueprint, get_root_file, get_cleanup_artifacts, get_workdir_keep_extra
from utils.prompt_loader import load_stack_prompt

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# Répertoires système à préserver lors du nettoyage inter-runs (invariants multi-stack)
_WORKDIR_KEEP_SYSTEM = {"logs", "config", "snapshots", "__pycache__", ".git"}


def _clean_project_workdir(workdir: str, extra_keep: set[str] | None = None) -> None:
    """
    Supprime les fichiers source du run précédent dans FACTORY_WORKDIR.

    Problème : le cleanup de fin de run ne supprime que node_modules/.next/__pycache__.
    Les fichiers source (package.json, app/, middleware.ts…) restent sur disque.
    Au run suivant, le LLM appelle read_files, voit ces fichiers, conclut que le
    projet est déjà généré et ne produit que jest.setup.js → SEMANTIC_VIOLATION.

    Solution : supprimer tous les fichiers/dossiers non-système en début de run.
    extra_keep : répertoires stack-spécifiques à préserver (ex: node_modules pour Node.js).
    """
    keep = _WORKDIR_KEEP_SYSTEM | (extra_keep or set())
    if not workdir or not os.path.isdir(workdir):
        return
    try:
        for item in os.listdir(workdir):
            if item in keep:
                continue
            full = os.path.join(workdir, item)
            try:
                if os.path.isfile(full) or os.path.islink(full):
                    os.remove(full)
                    logger.info(f"[pre-run cleanup] Fichier supprimé : {item}")
                elif os.path.isdir(full):
                    shutil.rmtree(full, ignore_errors=True)
                    logger.info(f"[pre-run cleanup] Répertoire supprimé : {item}")
            except Exception as item_err:
                logger.warning(f"[pre-run cleanup] Impossible de supprimer {item}: {item_err}")
    except Exception as e:
        logger.warning(f"[pre-run cleanup] Erreur listage workdir '{workdir}': {e}")


def _write_template_files(workdir: str, stack_cfg: dict, project_name: str, stack_id: str) -> dict:
    """
    Écrit les fichiers templates sur disque AVANT la boucle LLM.
    Ces fichiers sont invariants pour la stack — le LLM ne doit pas les régénérer.
    Retourne {nom_fichier: contenu} des fichiers écrits.
    """
    import pathlib
    templated = stack_cfg.get("templated_files", {})
    if not templated or not workdir:
        return {}

    # Répertoire base : factory-sprint0/config/stacks/{stack_id}/
    base_dir = pathlib.Path(__file__).parent.parent / "config" / "stacks" / stack_id

    written = {}
    for dest_filename, template_rel_path in templated.items():
        try:
            template_path = base_dir / template_rel_path
            if not template_path.exists():
                logger.warning(f"[templates] Template introuvable: {template_path}")
                continue
            content = template_path.read_text(encoding="utf-8")
            content = content.replace("{project_name}", project_name)
            dest_path = pathlib.Path(workdir) / dest_filename
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(content, encoding="utf-8")
            written[dest_filename] = content
            logger.info(f"[templates] ✓ {dest_filename} écrit depuis template")
        except Exception as e:
            logger.warning(f"[templates] Erreur écriture {dest_filename}: {e}")
    return written


# --- Dev Agent v3 Ultimate – Version 3.2 Breakthrough (Premier SaaS imminent) ---
def dev_agent(
    spec: str,
    mermaid: str,
    project_name: str = "default-project",
    run_id: str = "",
    stack_id: str = "",
    requirements: list = None,
    spec_unmatched: list = None,
) -> dict:
    """
    Dev Agent v3 Ultimate – Version finale stable.
    Correction boucle jest.config.js + détection run_build + progression forcée.
    """
    # Nettoyage du workdir avant toute génération — évite la contamination inter-runs.
    _workdir = os.getenv("FACTORY_WORKDIR", "")
    _extra_keep = set(get_workdir_keep_extra(stack_id)) if stack_id else set()
    if _workdir:
        _clean_project_workdir(_workdir, extra_keep=_extra_keep)

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    tools_phase1 = [write_file, validate_syntax, prisma_migrate, rag_search, read_files]
    tools_phase2 = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tool_map = {tool.name: tool for tool in tools_phase2}

    MAX_ITERATIONS = 10
    MAX_BUILD_ATTEMPTS = 8
    PHASE1_LIMIT = 7  # iterations 1-7 : génération ; iterations 8-10 : correction build
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
        # Le budget s'applique UNIQUEMENT aux tours supplémentaires (pas aux messages initiaux
        # qui sont toujours conservés). Sinon messages[1] (spec + RAG context ≈ 16 000 chars)
        # dépasse MAX_MAIN_HISTORY_CHARS à lui seul → aucun tour récent n'est jamais inclus
        # → le LLM ne voit jamais son historique et boucle sur la même instruction.
        current_chars = 0

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

    effective_stack_id = stack_id or get_stack_id()
    prompt = load_stack_prompt("dev", effective_stack_id)
    from .stack_config import load_stack_config
    stack_cfg = load_stack_config(effective_stack_id) or {}

    # ── Écriture des fichiers templates AVANT la boucle LLM ──────────────────
    # Ces fichiers sont invariants pour la stack. Le LLM ne doit pas les régénérer.
    _template_written = _write_template_files(_workdir, stack_cfg, project_name, effective_stack_id)
    _templated_names = set(_template_written.keys())

    blueprint = get_blueprint(effective_stack_id)
    required_files = blueprint.get("required_files", []) if isinstance(blueprint, dict) else []
    mandatory_rag_queries = stack_cfg.get("mandatory_rag_queries", [])
    mandatory_rag_context_chunks = []
    for query in mandatory_rag_queries:
        try:
            rag_result = rag_search.invoke({"query": query})
            mandatory_rag_context_chunks.append(f"[RAG::{query}]\n{str(rag_result)[:2500]}")
        except Exception as rag_err:
            mandatory_rag_context_chunks.append(f"[RAG::{query}] ERROR: {rag_err}")
    mandatory_rag_context = "\n\n".join(mandatory_rag_context_chunks)

    # Exclure les fichiers templates de l'ordre de génération LLM
    llm_required_files = [f for f in required_files if f not in _templated_names]
    templates_block = ""
    if _templated_names:
        templates_block = (
            "FICHIERS DÉJÀ ÉCRITS PAR LA FACTORY (templates validés — NE PAS RÉÉCRIRE) :\n"
            + "\n".join(f"  ✓ {f}" for f in sorted(_templated_names))
            + "\nCes fichiers sont corrects sur le disque. Concentre-toi sur les fichiers MÉTIER ci-dessous.\n\n"
        )
    required_files_block = ""
    if llm_required_files:
        required_files_block = (
            "ORDRE DE GÉNÉRATION OBLIGATOIRE — respecte cette séquence exacte, un fichier à la fois :\n"
            + "\n".join(f"{i+1}. {f}" for i, f in enumerate(llm_required_files))
            + "\nNe génère PAS de fichiers hors de cette liste avant que tous soient créés.\n\n"
        )
    requirements_block = ""
    if requirements:
        reqs_list = "\n".join(f"  - {r}" for r in requirements)
        requirements_block = (
            "FONCTIONNALITÉS OBLIGATOIRES — chaque item DOIT être implémenté dans les fichiers générés :\n"
            f"{reqs_list}\n"
            "⚠️ Tu ne peux pas déclarer le run terminé avant d'avoir créé UN fichier par page et par route API listée ci-dessus. "
            "Vérifie cette liste avant chaque appel à run_build.\n\n"
        )
    spec_degraded_block = ""
    if spec_unmatched:
        unmatched_list = "\n".join(f"  - {r}" for r in spec_unmatched)
        spec_degraded_block = (
            "⚠️ NOMS CANONIQUES OBLIGATOIRES — PRIORITÉ ABSOLUE SUR LA SPEC\n"
            "La spec a été générée avec des noms qui diffèrent des requirements du client.\n"
            "Pour les éléments ci-dessous, IGNORER les noms de la spec et utiliser EXACTEMENT ceux des requirements :\n"
            f"{unmatched_list}\n"
            "Règle absolue : si la spec nomme un modèle 'Article', le client exige 'Post'. "
            "Si la spec utilise '/articles', le client exige '/blog'. "
            "Tu dois implémenter les noms des requirements MOT POUR MOT — pas leurs équivalents dans la spec.\n\n"
        )
    packages = stack_cfg.get("packages", {})
    packages_block = ""
    if packages:
        packages_block = (
            "VERSIONS DE PACKAGES OBLIGATOIRES (copier exactement dans package.json, ne pas modifier) :\n"
            + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
            + "\n\n"
        )
    dev_packages = stack_cfg.get("dev_packages", {})
    dev_packages_block = ""
    if dev_packages:
        dev_packages_block = (
            "DEV DEPENDENCIES OBLIGATOIRES (copier exactement dans devDependencies) :\n"
            + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in dev_packages.items())
            + "\n\n"
        )
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"{spec_degraded_block}"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            f"Contexte RAG obligatoire (préchargé) :\n{mandatory_rag_context}\n\n"
            f"{packages_block}"
            f"{dev_packages_block}"
            f"{templates_block}"
            f"{required_files_block}"
            f"{requirements_block}"
            "⚠️ RÈGLE ABSOLUE — package.json DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE (avant jest.setup.js, avant app/layout.tsx, avant tout). "
            "Étape 1 OBLIGATOIRE : génère IMMÉDIATEMENT package.json avec les versions exactes ci-dessus. "
            "Ne génère AUCUN autre fichier avant que package.json soit écrit sur le disque."
        ))
    ]

    files = {}
    # Pré-populer files avec le contenu des templates (comptabilisés comme déjà écrits)
    files.update(_template_written)
    final_message = ""
    build_attempts = 0
    build_attempted = False
    build_success = False
    last_build_succeeded = False  # True uniquement quand run_build() confirme un succès réel
    last_build_error = ""
    last_build_error_full = ""
    last_test_error = ""
    last_test_error_full = ""
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

    def _find_project_dir(files_dict: dict) -> str:
        """
        Déduit le répertoire racine du projet à partir des fichiers écrits.
        Hard rule (couche Code) : si le LLM a écrit sous un sous-répertoire
        (ex: 'my-saas/package.json'), retourne ce sous-répertoire ('my-saas').
        Sinon retourne '.'. Corrige le bug working-directory FORCED_RUN_BUILD.
        Le fichier racine de référence est lu depuis la stack config (root_file),
        ce qui rend la détection compatible avec toutes les stacks futures.
        """
        try:
            from agents.stack_config import get_root_file
            root_file = get_root_file(effective_stack_id)
        except Exception:
            root_file = "package.json"
        root_filename = root_file.split("/")[-1]
        for p in files_dict.keys():
            normalized = p.replace("\\", "/")
            if normalized == root_file or normalized.endswith("/" + root_filename):
                parent = normalized.rsplit("/", 1)[0] if "/" in normalized else ""
                return parent if parent else "."
        return "."

    stagnant_iterations = 0
    key_files = required_files or ["package.json"]
    for iteration in range(1, MAX_ITERATIONS + 1):
        current_phase = 1 if iteration <= PHASE1_LIMIT else 2
        current_tools = tools_phase1 if current_phase == 1 else tools_phase2
        logger.info(f"[DEV AGENT v3.2] Itération {iteration}/{MAX_ITERATIONS} | Phase {current_phase} | Build attempts: {build_attempts}")

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
        response = llm.bind_tools(current_tools).invoke(main_messages)
        messages.append(response)

        tool_messages = []
        raw_tool_outputs = []
        wrote_file_this_iter = False
        called_build_this_iter = False
        build_failed_this_iter = False
        if response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_to_call = tool_map.get(tool_name)
                if tool_to_call:
                    try:
                        # Hard rule: corrige project_dir pour run_build si le LLM passe '.'
                        # alors que les fichiers sont sous un sous-répertoire.
                        call_args = tool_call["args"]
                        if tool_name == "run_build":
                            computed_dir = _find_project_dir(files)
                            if computed_dir != "." and call_args.get("project_dir", ".") == ".":
                                call_args = {**call_args, "project_dir": computed_dir}
                                logger.info(f"[run_build] project_dir corrigé: '.' → '{computed_dir}'")
                            # ── BLUEPRINT VALIDATOR BLOQUANT (Sprint 4) ──────────────────────
                            _present = set(files.keys()) | _templated_names
                            _blueprint_missing = [
                                f for f in required_files
                                if not any(f in p for p in _present)
                            ]
                            if _blueprint_missing:
                                _block_msg = (
                                    "BLUEPRINT VALIDATOR — BUILD BLOQUÉ\n"
                                    f"{len(_blueprint_missing)} fichier(s) obligatoire(s) manquant(s) :\n"
                                    + "\n".join(f"  - {f}" for f in _blueprint_missing)
                                    + "\n\nGénère ces fichiers avec write_file() maintenant."
                                    " run_build sera disponible une fois tous présents."
                                )
                                tool_messages.append(ToolMessage(content=_block_msg, tool_call_id=tool_call["id"]))
                                logger.warning(f"[BlueprintValidator] BUILD BLOQUÉ — {len(_blueprint_missing)} manquant(s): {_blueprint_missing}")
                                build_attempted = True
                                called_build_this_iter = True
                                continue  # ne pas exécuter run_build
                            # ── USE_STATE TYPED GUARD (Sprint 5) ─────────────────────────────
                            # useState([]) sans type → TypeScript strict infère never[]
                            # → build échoue systématiquement sur "Property 'x' does not exist on type 'never'"
                            # → corrige avant run_build pour ne pas gaspiller une tentative de build
                            _BUSINESS_PREFIXES = ("app/", "components/", "src/app/", "src/components/")
                            _usestate_violations = []
                            for _fp, _fc in files.items():
                                _fp_norm = _fp.replace("\\", "/")
                                _is_business = any(_fp_norm.startswith(pfx) for pfx in _BUSINESS_PREFIXES)
                                if not _is_business:
                                    continue
                                if re.search(r'\buseState\s*\(\s*\[\s*\]\s*\)', _fc) and not re.search(r'\buseState\s*<', _fc):
                                    _usestate_violations.append(_fp_norm)
                            if _usestate_violations:
                                _us_msg = (
                                    "USE_STATE TYPED GUARD — BUILD BLOQUÉ\n"
                                    "useState([]) sans annotation de type détecté — TypeScript strict infère never[], "
                                    "ce qui provoque 'Property does not exist on type never' au build.\n"
                                    "Fichiers concernés :\n"
                                    + "\n".join(f"  - {f}" for f in _usestate_violations)
                                    + "\n\nCorrige chaque occurrence : useState<Type[]>([]) avant d'appeler run_build."
                                )
                                tool_messages.append(ToolMessage(content=_us_msg, tool_call_id=tool_call["id"]))
                                logger.warning(f"[UseStateGuard] BUILD BLOQUÉ — useState non typé dans : {_usestate_violations}")
                                build_attempted = True
                                called_build_this_iter = True
                                continue  # ne pas exécuter run_build
                            # ── PRISMA IMPORT GUARD (Sprint 5) ───────────────────────────────
                            # import { prisma } from '@prisma/client' est invalide en Prisma 7 :
                            # @prisma/client exporte uniquement PrismaClient (la classe), pas un singleton.
                            # Détection pré-build → bloc bloquant → LLM génère lib/prisma.ts et corrige les imports.
                            _PRISMA_BAD_IMPORT = re.compile(
                                r'import\s*\{[^}]*\bprisma\b[^}]*\}\s*from\s*[\'"]@prisma/client[\'"]',
                                re.MULTILINE,
                            )
                            _SERVER_PREFIXES = ("app/", "pages/", "src/app/", "src/pages/", "lib/")
                            _prisma_import_violations = []
                            for _fp, _fc in files.items():
                                _fp_norm = _fp.replace("\\", "/")
                                if not any(_fp_norm.startswith(pfx) for pfx in _SERVER_PREFIXES):
                                    continue
                                if _PRISMA_BAD_IMPORT.search(_fc):
                                    _prisma_import_violations.append(_fp_norm)
                            if _prisma_import_violations:
                                _prisma_msg = (
                                    "PRISMA IMPORT GUARD — BUILD BLOQUÉ\n"
                                    "import { prisma } from '@prisma/client' est invalide en Prisma 7.\n"
                                    "@prisma/client exporte uniquement PrismaClient (la classe), pas un singleton 'prisma'.\n"
                                    "Fichiers concernés :\n"
                                    + "\n".join(f"  - {f}" for f in _prisma_import_violations)
                                    + "\n\nCORRECTION OBLIGATOIRE EN 2 ÉTAPES :\n"
                                    "1. Crée lib/prisma.ts avec ce contenu exact :\n"
                                    "   import { PrismaClient } from '@prisma/client';\n"
                                    "   const prisma = new PrismaClient();\n"
                                    "   export default prisma;\n"
                                    "2. Dans chaque fichier concerné, remplace l'import invalide par :\n"
                                    "   import prisma from '@/lib/prisma';\n"
                                    "Appelle write_file() pour ces corrections, PUIS appelle run_build."
                                )
                                tool_messages.append(ToolMessage(content=_prisma_msg, tool_call_id=tool_call["id"]))
                                logger.warning(f"[PrismaImportGuard] BUILD BLOQUÉ — import invalide dans : {_prisma_import_violations}")
                                build_attempted = True
                                called_build_this_iter = True
                                continue  # ne pas exécuter run_build
                            # ── GUARD C : @/lib/prisma import sans lib/prisma.ts (Sprint 5) ─────
                            # Le LLM utilise correctement `import prisma from '@/lib/prisma'`
                            # mais oublie de créer lib/prisma.ts → Module not found au build.
                            _LIB_PRISMA_IMPORT = re.compile(
                                r'''import\s+\w+\s+from\s+['"]@/lib/prisma['"]''',
                                re.MULTILINE,
                            )
                            _files_norm = {fp.replace("\\", "/"): fc for fp, fc in files.items()}
                            _uses_lib_prisma = any(
                                _LIB_PRISMA_IMPORT.search(fc)
                                for fc in _files_norm.values()
                            )
                            _has_lib_prisma_ts = any(
                                fp in ("lib/prisma.ts", "src/lib/prisma.ts")
                                for fp in _files_norm
                            )
                            if _uses_lib_prisma and not _has_lib_prisma_ts:
                                _guard_c_msg = (
                                    "GUARD C — BUILD BLOQUÉ : lib/prisma.ts manquant\n"
                                    "Des fichiers importent `prisma` depuis '@/lib/prisma' mais lib/prisma.ts "
                                    "n'existe pas dans le projet.\n\n"
                                    "CORRECTION : appelle write_file('lib/prisma.ts') avec ce contenu EXACT :\n"
                                    "  import { PrismaClient } from '@prisma/client';\n"
                                    "  const prisma = new PrismaClient();\n"
                                    "  export default prisma;\n\n"
                                    "Ensuite appelle run_build."
                                )
                                tool_messages.append(ToolMessage(content=_guard_c_msg, tool_call_id=tool_call["id"]))
                                logger.warning("[GuardC] BUILD BLOQUÉ — @/lib/prisma importé mais lib/prisma.ts absent")
                                build_attempted = True
                                called_build_this_iter = True
                                continue  # ne pas exécuter run_build
                            # ── GUARD D : hooks React sans "use client" (Sprint 5) ───────────────
                            # useState/useEffect dans un Server Component → erreur de compilation.
                            # Détecte les fichiers app/**/*.tsx (hors app/api/**) qui utilisent
                            # des hooks React sans la directive "use client" en tête de fichier.
                            _HOOKS_RE = re.compile(
                                r'\b(useState|useEffect|useRef|useCallback|useMemo|useReducer|useContext)\s*[(<]',
                                re.MULTILINE,
                            )
                            _USE_CLIENT_RE = re.compile(r'''^\s*['"]use client['"]''', re.MULTILINE)
                            _guard_d_violations = []
                            for _fp, _fc in _files_norm.items():
                                if not _fp.startswith("app/"):
                                    continue
                                if _fp.startswith("app/api/"):
                                    continue
                                if not _fp.endswith(".tsx") and not _fp.endswith(".jsx"):
                                    continue
                                if _HOOKS_RE.search(_fc) and not _USE_CLIENT_RE.search(_fc):
                                    _guard_d_violations.append(_fp)
                            if _guard_d_violations:
                                _guard_d_msg = (
                                    "GUARD D — BUILD BLOQUÉ : directive \"use client\" manquante\n"
                                    "Les fichiers suivants utilisent des hooks React (useState, useEffect…) "
                                    "sans la directive \"use client\" en première ligne :\n"
                                    + "\n".join(f"  - {f}" for f in _guard_d_violations)
                                    + "\n\nCORRECTION : ajoute '\"use client\";' comme PREMIÈRE ligne "
                                    "(avant tous les imports) dans chaque fichier concerné, "
                                    "puis appelle run_build."
                                )
                                tool_messages.append(ToolMessage(content=_guard_d_msg, tool_call_id=tool_call["id"]))
                                logger.warning(f"[GuardD] BUILD BLOQUÉ — hooks sans 'use client' dans : {_guard_d_violations}")
                                build_attempted = True
                                called_build_this_iter = True
                                continue  # ne pas exécuter run_build
                        logger.info(f"Exécution tool: {tool_name}")
                        output = tool_to_call.invoke(call_args)
                        raw_output = str(output)
                        raw_tool_outputs.append(raw_output)

                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            if "Build successful" in raw_output:
                                last_build_succeeded = True  # build réel confirmé
                                build_success = True
                                build_attempts = 0
                                last_build_error = ""
                                last_build_error_full = ""
                                last_failed_command = ""
                            else:
                                build_failed_this_iter = True
                                extracted_stderr = _extract_stderr(raw_output)
                                last_build_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_build_error = last_build_error_full[:2000]
                                failed_cmd = _extract_failed_command(raw_output)
                                if failed_cmd:
                                    last_failed_command = failed_cmd

                        if tool_name == "run_tests":
                            if "Tests passed" in raw_output:
                                last_test_error = ""
                                last_test_error_full = ""
                            else:
                                extracted_stderr = _extract_stderr(raw_output)
                                last_test_error_full = extracted_stderr if extracted_stderr else raw_output
                                last_test_error = last_test_error_full[:2000]

                        shrunk_output = _shrink_tool_output(tool_name, raw_output)
                        tool_messages.append(ToolMessage(content=shrunk_output, tool_call_id=tool_call["id"]))
                    except Exception as e:
                        error_text = f"ERREUR {tool_name}: {e}"
                        raw_tool_outputs.append(error_text)
                        if tool_name == "run_build":
                            build_attempted = True
                            called_build_this_iter = True
                            build_failed_this_iter = True
                            last_build_error = error_text[:2000]
                            last_build_error_full = error_text
                            last_failed_command = "run_build"
                        if tool_name == "run_tests":
                            last_test_error = error_text[:2000]
                            last_test_error_full = error_text
                        tool_messages.append(ToolMessage(content=error_text, tool_call_id=tool_call["id"]))
                else:
                    if tool_name == "run_build" and current_phase == 1:
                        tool_messages.append(
                            ToolMessage(
                                content="Génération non terminée, continue d'écrire les fichiers",
                                tool_call_id=tool_call["id"],
                            )
                        )
                    else:
                        tool_messages.append(ToolMessage(content=f"Tool {tool_name} inconnu", tool_call_id=tool_call["id"]))

            messages.extend(tool_messages)

            for tc in response.tool_calls:
                if tc["name"] == "write_file":
                    path = tc["args"].get("path")
                    content = tc["args"].get("content")
                    if path and content is not None:
                        # Lire le contenu réel depuis le disque après sanitize,
                        # pour que files[path] == ce que test_coverage_agent utilisera.
                        try:
                            workdir = os.getenv("FACTORY_WORKDIR", ".")
                            disk_path = os.path.normpath(os.path.join(workdir, path))
                            with open(disk_path, "r", encoding="utf-8") as _df:
                                files[path] = _df.read()
                        except Exception:
                            files[path] = content  # fallback si lecture échoue
                        wrote_file_this_iter = True
                        logger.info(f"Fichier généré : {path}")

        # Détection build succès/échec déterministe: uniquement depuis run_build.
        if build_failed_this_iter:
            build_attempts += 1

        if wrote_file_this_iter or called_build_this_iter:
            stagnant_iterations = 0
        else:
            stagnant_iterations += 1

        # ── Guard Phase 1 : primary_manifest DOIT être le premier fichier écrit ──────
        # Lecture depuis stack config (multi-stack safe) au lieu de hardcoder "package.json".
        _primary = get_root_file(stack_id) if stack_id else "package.json"
        if current_phase == 1 and wrote_file_this_iter and _primary not in files:
            non_pkg_files = [
                tc["args"].get("path", "")
                for tc in response.tool_calls
                if tc["name"] == "write_file" and tc["args"].get("path", "") != _primary
            ]
            if non_pkg_files:
                logger.warning(
                    f"[PHASE1_SEQUENCE_VIOLATION] Fichier(s) écrit(s) avant {_primary} : {non_pkg_files}"
                )
                messages.append(HumanMessage(content=(
                    f"⚠️ ERREUR DE SÉQUENCE CRITIQUE : Tu as écrit {non_pkg_files} avant {_primary}.\n"
                    f"RÈGLE ABSOLUE : {_primary} DOIT être le PREMIER fichier généré, AVANT TOUT AUTRE.\n"
                    f"ACTION OBLIGATOIRE IMMÉDIATE : génère {_primary} maintenant avec les versions exactes :\n"
                    + "\n".join(f'  "{pkg}": "{ver}"' for pkg, ver in packages.items())
                    + f"\n\nNe génère AUCUN autre fichier avant que {_primary} soit écrit."
                )))

        # Forçage progression si fichiers clés présents — Phase 2 seulement
        _pdir = _find_project_dir(files)  # Hard rule: répertoire réel du projet
        if current_phase == 2 and all(any(k in p for p in files) for k in key_files) and not build_success:
            messages.append(HumanMessage(content=f"Fichiers clés présents. Appelle run_build(project_dir='{_pdir}') maintenant pour valider le projet."))

        # Transition Phase 1 → Phase 2 : compléter les manquants puis build
        if iteration == PHASE1_LIMIT and not build_success:
            _missing_required = [f for f in required_files if not any(f in p for p in files)]
            _missing_block = (
                "FICHIERS OBLIGATOIRES MANQUANTS — génère-les EN PREMIER, avant tout run_build :\n"
                + "\n".join(f"- {f}" for f in _missing_required)
                + "\n\n"
            ) if _missing_required else ""
            messages.append(HumanMessage(content=(
                "PHASE 2 — COMPLÉTION + BUILD\n"
                f"Fichiers présents : {list(files.keys())}\n\n"
                f"{_missing_block}"
                f"Une fois tous les fichiers obligatoires générés, appelle run_build(project_dir='{_pdir}') "
                "et corrige toutes les erreurs retournées jusqu'au succès."
            )))

        # Garde-fou: si le modele stagne sans progres, forcer un run_build — Phase 2 seulement.
        if current_phase == 2 and not build_success and not called_build_this_iter and (stagnant_iterations >= 2 or iteration >= MAX_ITERATIONS - 1):
            # ── BLUEPRINT VALIDATOR BLOQUANT — stagnation guard (Sprint 4) ──────
            _stag_present = set(files.keys()) | _templated_names
            _stag_missing = [
                f for f in required_files
                if not any(f in p for p in _stag_present)
            ]
            if _stag_missing:
                messages.append(HumanMessage(content=(
                    "BLUEPRINT VALIDATOR — STAGNATION DÉTECTÉE\n"
                    f"Le build ne peut pas être lancé. {len(_stag_missing)} fichier(s) obligatoire(s) manquant(s) :\n"
                    + "\n".join(f"  - {f}" for f in _stag_missing)
                    + "\n\nGénère ces fichiers avec write_file() maintenant. Ne lance PAS run_build avant."
                )))
                logger.warning(f"[BlueprintValidator] STAGNATION — BUILD INTERDIT, manquants: {_stag_missing}")
                stagnant_iterations = 0  # reset pour laisser l'agent corriger
            else:
                # ── fin Blueprint Validator — tous les fichiers présents, build autorisé ──
                forced_build_output = str(run_build.invoke({"project_dir": _pdir}))
                build_attempted = True
                called_build_this_iter = True
                raw_tool_outputs.append(forced_build_output)
                messages.append(HumanMessage(content=f"[FORCED_RUN_BUILD]\n{_shrink_tool_output('run_build', forced_build_output)}"))
                if "Build successful" in forced_build_output:
                    last_build_succeeded = True  # build réel confirmé (chemin forcé)
                    build_success = True
                    build_attempts = 0
                    last_build_error = ""
                    last_build_error_full = ""
                    last_failed_command = ""
                else:
                    build_attempts += 1
                    extracted_stderr = _extract_stderr(forced_build_output)
                    last_build_error_full = extracted_stderr if extracted_stderr else forced_build_output
                    last_build_error = last_build_error_full[:2000]
                    failed_cmd = _extract_failed_command(forced_build_output)
                    if failed_cmd:
                        last_failed_command = failed_cmd

        # Reflection informative uniquement (ne pilote pas la sortie).
        reflection_messages = [
            SystemMessage(content=(
                "État actuel :\n"
                f"Fichiers générés : {list(files.keys())}\n"
                f"Build attempts : {build_attempts}/{MAX_BUILD_ATTEMPTS}\n"
                f"Dernière erreur build : {last_build_error[:500] if last_build_error else 'N/A'}\n"
                f"Dernière commande en échec : {last_failed_command or 'N/A'}\n"
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

        # Sortie déterministe: uniquement sur résultat build confirmé.
        if last_build_succeeded:
            logger.info("SUCCESS TOTAL : build confirmé, sortie de boucle.")
            build_success = True
            break

        if build_attempts >= MAX_BUILD_ATTEMPTS:
            final_message = "ÉCHEC : ERREUR RÉCURRENTE BUILD"
            break

    # Nettoyage scopé au répertoire projet — artifacts lus depuis stack config (multi-stack safe).
    cleanup_dir = _find_project_dir(files)
    for _artifact in get_cleanup_artifacts(stack_id) if stack_id else [".next", "node_modules"]:
        shutil.rmtree(os.path.join(cleanup_dir, _artifact), ignore_errors=True)
    shutil.rmtree(os.path.join(cleanup_dir, "__pycache__"), ignore_errors=True)

    if not build_attempted and not build_success:
        final_message = "BuildNotAttempted: run_build n'a pas ete execute."

    # Création du fichier de méta-données du run dans le répertoire projet.
    try:
        meta = {
            "run_id": run_id,
            "stack_id": effective_stack_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workflow_version": "sprint3",
        }
        meta_path = os.path.join(cleanup_dir, ".factory-meta.json")
        with open(meta_path, "w", encoding="utf-8") as _mf:
            json.dump(meta, _mf, indent=2)
        logger.info(f"[meta] .factory-meta.json créé : run_id={run_id}")
    except Exception as _me:
        logger.warning(f"[meta] Impossible de créer .factory-meta.json: {_me}")

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
            "last_build_error_full": last_build_error_full if last_build_error_full else "",
            "last_test_error": last_test_error[:2000] if last_test_error else "",
            "last_test_error_full": last_test_error_full if last_test_error_full else "",
            "last_failed_command": last_failed_command,
        },
    }
