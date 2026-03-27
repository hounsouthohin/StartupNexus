import os
import json
import logging
import shutil
from pathlib import PurePosixPath
from datetime import datetime, timezone

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
from .dev_compat import ChatOpenAI, HumanMessage, SystemMessage, ToolMessage, LLMConversationRunner
from .stack_config import get_blueprint, get_cleanup_artifacts, get_workdir_keep_extra
from utils.prompt_loader import load_stack_prompt
from .file_supervision_loop import FileSupervisionLoop
from .dev_path_utils import (
    make_priority_ranker,
    sort_paths_by_priority,
    resolve_max_iterations,
    extract_primary_path_from_requirement,
    find_project_dir,
)
from .pre_build_validator import PreBuildValidator
from .build_state_manager import BuildStateManager, RunStateComputer
from .dev_file_ops import clean_project_workdir, write_template_files
from .dev_loop import run_dev_loop

# Logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")



# --- Dev Agent v3 Ultimate – Version 3.2 Breakthrough (Premier SaaS imminent) ---
def dev_agent(
    spec: str,
    mermaid: str,
    project_name: str = "default-project",
    run_id: str = "",
    stack_id: str = "",
    requirements: list = None,
    spec_unmatched: list = None,
    plan: dict = None,
) -> dict:
    """
    Dev Agent v3 Ultimate – Version finale stable.
    Correction boucle jest.config.js + détection run_build + progression forcée.
    """
    # Nettoyage du workdir avant toute génération — évite la contamination inter-runs.
    _workdir = os.getenv("FACTORY_WORKDIR", "")
    _extra_keep = set(get_workdir_keep_extra(stack_id)) if stack_id else set()
    if _workdir:
        clean_project_workdir(_workdir, extra_keep=_extra_keep)

    # max_retries=3 couvre les 429 transitoires avec backoff LangChain.
    # with_fallbacks non applicable ici : bind_tools n'est pas disponible
    # sur RunnableWithFallbacks — fallback model pour dev différé (T007.5).
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=3)

    # Tous les outils disponibles dès l'itération 1 — le Blueprint Validator bloque
    # run_build si des fichiers obligatoires manquent (gate suffisant).
    # Supprimer le split Phase1/Phase2 qui causait 55% des runs à atteindre MAX_ITERATIONS.
    tools_phase1 = [write_file, validate_syntax, prisma_migrate, rag_search, read_files, run_build]
    tools_phase2 = tools_phase1
    tool_map = {tool.name: tool for tool in tools_phase1}

    DEFAULT_MAX_ITERATIONS = 14
    MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
    MAX_BUILD_ATTEMPTS = 8
    PHASE1_LIMIT = MAX_ITERATIONS  # aligné dynamiquement après chargement stack
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
        except Exception:
            return text[:int(max_tokens * 3.5)] + "\n\n[TRUNCATED]"

    summarized_spec = summarize_text(spec, MAX_SPEC_TOKENS, "Specification")
    summarized_mermaid = summarize_text(mermaid, MAX_MERMAID_TOKENS, "Mermaid Diagram")

    effective_stack_id = stack_id or get_stack_id()
    prompt = load_stack_prompt("dev", effective_stack_id)
    from .stack_config import load_stack_config
    stack_cfg = load_stack_config(effective_stack_id) or {}
    try:
        _supervision_routing = load_stack_config(
            stack_id or "nextjs-clerk-prisma"
        ).get("supervision_routing", {})
    except Exception:
        _supervision_routing = {}
    _supervision_cfg = stack_cfg.get("supervision", {}) if isinstance(stack_cfg, dict) else {}
    try:
        _supervision_batch_size = int(_supervision_cfg.get("batch_size", 3))
    except Exception:
        _supervision_batch_size = 3
    if _supervision_batch_size < 1:
        _supervision_batch_size = 1
    try:
        _supervisor_timeout_ms = int(_supervision_cfg.get("supervisor_timeout_ms", 30000))
    except Exception:
        _supervisor_timeout_ms = 30000
    if _supervisor_timeout_ms < 1:
        _supervisor_timeout_ms = 30000

    generation_order_cfg = stack_cfg.get("generation_order", {}) if isinstance(stack_cfg, dict) else {}
    _priority_paths_cfg = generation_order_cfg.get("priority_paths", []) if isinstance(generation_order_cfg, dict) else []
    _path_priority_ranker = make_priority_ranker(_priority_paths_cfg)

    MAX_ITERATIONS = resolve_max_iterations(stack_cfg, requirements, default=DEFAULT_MAX_ITERATIONS)
    PHASE1_LIMIT = MAX_ITERATIONS
    logger.info(
        f"[ITERATION_POLICY] requirements={len(requirements or [])} "
        f"max_iterations={MAX_ITERATIONS}"
    )

    # ── Écriture des fichiers templates AVANT la boucle LLM ──────────────────
    # Ces fichiers sont invariants pour la stack. Le LLM ne doit pas les régénérer.
    _template_written = write_template_files(_workdir, stack_cfg, project_name, effective_stack_id)
    _templated_names = set(_template_written.keys())

    blueprint = get_blueprint(effective_stack_id)
    required_files = blueprint.get("required_files", []) if isinstance(blueprint, dict) else []
    mandatory_rag_queries = stack_cfg.get("mandatory_rag_queries", [])
    try:
        mandatory_rag_k = int(stack_cfg.get("mandatory_rag_k", 4))
    except Exception:
        mandatory_rag_k = 4
    try:
        mandatory_rag_snippet_chars = int(stack_cfg.get("mandatory_rag_snippet_chars", 900))
    except Exception:
        mandatory_rag_snippet_chars = 900
    mandatory_rag_context_chunks = []
    for query in mandatory_rag_queries:
        try:
            rag_result = rag_search.invoke({"query": query, "k": mandatory_rag_k})
            mandatory_rag_context_chunks.append(
                f"[RAG::{query}]\n{str(rag_result)[:mandatory_rag_snippet_chars]}"
            )
        except Exception as rag_err:
            mandatory_rag_context_chunks.append(f"[RAG::{query}] ERROR: {rag_err}")
    mandatory_rag_context = "\n\n".join(mandatory_rag_context_chunks)

    # scaffold_extends : fichiers pré-écrits par template mais étendus par le LLM (ex: prisma/schema.prisma).
    # Ils sont exemptés du bloc "NE PAS RÉÉCRIRE" et restent dans llm_required_files.
    scaffold_extends_cfg = stack_cfg.get("scaffold_extends", {})
    scaffold_extends_paths = set(scaffold_extends_cfg.keys())

    # Exclure les fichiers templates de l'ordre de génération LLM (sauf scaffold_extends)
    _templated_protected = _templated_names - scaffold_extends_paths
    llm_required_files = sort_paths_by_priority([f for f in required_files if f not in _templated_protected], _path_priority_ranker)
    templates_block = ""
    if _templated_protected:
        templates_block = (
            "FICHIERS DÉJÀ ÉCRITS PAR LA FACTORY (templates validés — NE PAS RÉÉCRIRE) :\n"
            + "\n".join(f"  ✓ {f}" for f in sorted(_templated_protected))
            + "\nCes fichiers sont corrects sur le disque. Concentre-toi sur les fichiers MÉTIER ci-dessous.\n\n"
        )
    # required_files_block : tous les fichiers obligatoires.
    # Pour les scaffold_extends, note courte sans mention "pré-écrit" (évite la paralysie).
    required_files_block = ""
    if llm_required_files:
        lines = []
        for i, f in enumerate(llm_required_files):
            if f in scaffold_extends_paths:
                kw = scaffold_extends_cfg[f].get("locked_until_keyword", "model ").strip()
                lines.append(f"{i+1}. {f}  ← écrire les blocs `{kw} NomDuModele {{...}}` du brief")
            else:
                lines.append(f"{i+1}. {f}")
        required_files_block = (
            "FICHIERS OBLIGATOIRES À CRÉER (en plus des fichiers métier de la spec) :\n"
            + "\n".join(lines)
            + "\n\n"
        )
    scaffold_schema_block = ""  # plus utilisé — logique fusionnée dans required_files_block
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
            "Règle absolue : si la spec nomme un modèle '<NomDansSpec>', le client exige '<NomDansRequirements>'. "
            "Si la spec utilise '/<cheminSpec>', le client exige '/<cheminRequirements>'. "
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
    # Bloc d'ordre adaptatif — basé sur llm_required_files (fichiers réellement à écrire par le LLM,
    # templates déjà exclus). Si package.json apparaît (templates non fonctionnels), il est
    # remonté en tête quelle que soit la priorité generation_order.
    # ordering_block : tous les fichiers obligatoires dans l'ordre de priorité.
    ordering_block = ""
    if llm_required_files:
        _ordered = list(llm_required_files)
        if "package.json" in _ordered:
            _ordered.remove("package.json")
            _ordered.insert(0, "package.json")
        ordering_block = (
            "══════════════════════════════════════════════════════════\n"
            "SÉQUENCE D'ÉCRITURE OBLIGATOIRE — respecter cet ordre AVANT tout autre fichier :\n"
            + "\n".join(f"  {i+1}. {f}" for i, f in enumerate(_ordered))
            + "\n"
            "INTERDIT : run_build() ou tout fichier métier avant que TOUS ces fichiers soient écrits.\n"
            "══════════════════════════════════════════════════════════\n\n"
        )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=(
            f"Projet : {project_name}\n\n"
            f"{ordering_block}"
            f"{spec_degraded_block}"
            f"Spec :\n{summarized_spec}\n\n"
            f"Mermaid :\n{summarized_mermaid}\n\n"
            f"Contexte RAG obligatoire (préchargé) :\n{mandatory_rag_context}\n\n"
            f"{packages_block}"
            f"{dev_packages_block}"
            f"{templates_block}"
            f"{required_files_block}"
            f"{requirements_block}"
        ))
    ]
    runner = LLMConversationRunner(llm, messages)

    files = {}
    files.update(_template_written)

    _guard_warning_hits: dict[str, int] = {}
    _supervision_loop = FileSupervisionLoop(max_attempts=2)
    _validator = PreBuildValidator(
        stack_cfg=stack_cfg,
        required_files=required_files,
        templated_names=_templated_names,
        supervision_loop=_supervision_loop,
        scaffold_extends_paths=scaffold_extends_paths,
        stack_id=effective_stack_id,
        guard_warning_hits=_guard_warning_hits,
    )
    _run_state_computer = RunStateComputer(
        requirements=requirements,
        llm_required_files=llm_required_files,
        validator=_validator,
        path_priority_ranker=_path_priority_ranker,
        scaffold_extends_paths=scaffold_extends_paths,
    )

    _loop_state = run_dev_loop(
        llm,
        runner,
        messages,
        tools_phase1,
        tools_phase2,
        tool_map,
        files,
        _run_state_computer,
        _supervision_loop,
        _validator,
        stack_cfg,
        max_iterations=MAX_ITERATIONS,
        phase1_limit=PHASE1_LIMIT,
        max_build_attempts=MAX_BUILD_ATTEMPTS,
        project_name=project_name,
        run_id=run_id,
        stack_id=stack_id,
        effective_stack_id=effective_stack_id,
        plan=plan,
        requirements=requirements,
        scaffold_extends_paths=scaffold_extends_paths,
        packages=packages,
        supervision_routing=_supervision_routing,
        supervision_batch_size=_supervision_batch_size,
        supervisor_timeout_ms=_supervisor_timeout_ms,
        workdir=_workdir,
        required_files=required_files,
        templated_names=_templated_names,
    )

    files = _loop_state.files
    iteration = _loop_state.iteration
    build_attempts = _loop_state.build_attempts
    build_attempted = _loop_state.build_attempted
    build_success = _loop_state.build_success
    final_message = _loop_state.final_message
    _final_gate_source = _loop_state.final_gate_source
    _final_blocking_guard_id = _loop_state.final_blocking_guard_id
    _final_gate_message = _loop_state.final_gate_message
    _final_missing_required_files = _loop_state.final_missing_required_files
    _sup_files_reviewed = _loop_state.sup_files_reviewed
    _sup_corrections_count = _loop_state.sup_corrections_count
    _conformity_scores = _loop_state.conformity_scores
    _security_scores = _loop_state.security_scores
    _architecture_scores = _loop_state.architecture_scores
    _build_corrections_count = _loop_state.build_corrections_count
    _tsc_errors_caught = _loop_state.tsc_errors_caught
    _eslint_errors_caught = _loop_state.eslint_errors_caught
    _prisma_errors_caught = _loop_state.prisma_errors_caught
    last_build_error = _loop_state.last_build_error
    last_build_error_full = _loop_state.last_build_error_full
    last_test_error = _loop_state.last_test_error
    last_test_error_full = _loop_state.last_test_error_full
    last_failed_command = _loop_state.last_failed_command

    # Nettoyage scopé au répertoire projet — artifacts lus depuis stack config (multi-stack safe).
    _rel_dir = find_project_dir(files, effective_stack_id)
    _base = _workdir if _workdir else os.getcwd()
    project_abs = os.path.normpath(os.path.join(_base, _rel_dir))
    for _artifact in get_cleanup_artifacts(stack_id) if stack_id else [".next", "node_modules"]:
        shutil.rmtree(os.path.join(project_abs, _artifact), ignore_errors=True)
    shutil.rmtree(os.path.join(project_abs, "__pycache__"), ignore_errors=True)

    # Création du fichier de méta-données du run dans le répertoire projet.
    try:
        meta = {
            "run_id": run_id,
            "stack_id": effective_stack_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "workflow_version": "sprint3",
        }
        meta_path = os.path.join(project_abs, ".factory-meta.json")
        with open(meta_path, "w", encoding="utf-8") as _mf:
            json.dump(meta, _mf, indent=2)
        logger.info(f"[meta] .factory-meta.json créé : run_id={run_id}")
    except Exception as _me:
        logger.warning(f"[meta] Impossible de créer .factory-meta.json: {_me}")

    logger.info("Dev Agent v3.2 terminé.")
    _state_manager = BuildStateManager(
        iteration=iteration,
        build_attempts=build_attempts,
        build_attempted=build_attempted,
        build_success=build_success,
        final_message=final_message,
        gate_source=_final_gate_source,
        blocking_guard_id=_final_blocking_guard_id,
        gate_message=_final_gate_message,
        missing_required_files=_final_missing_required_files,
        guard_warning_hits=_guard_warning_hits,
        supervisor_files_reviewed=_sup_files_reviewed,
        supervisor_corrections_count=_sup_corrections_count,
        conformity_scores=list(_conformity_scores),
        security_scores=list(_security_scores),
        architecture_scores=list(_architecture_scores),
        build_corrections_count=_build_corrections_count,
        tsc_errors_caught=int(_tsc_errors_caught),
        eslint_errors_caught=int(_eslint_errors_caught),
        prisma_errors_caught=int(_prisma_errors_caught),
        last_build_error=last_build_error,
        last_build_error_full=last_build_error_full,
        last_test_error=last_test_error,
        last_test_error_full=last_test_error_full,
        last_failed_command=last_failed_command,
    )
    return {
        "files": files,
        "final_message": final_message,
        "success": build_success,
        "metadata": _state_manager.to_metadata(
            total_files=len(files),
            supervision_loop_corrections=_supervision_loop.corrections_count,
            supervision_loop_pending_at_end=len(_supervision_loop.pending_paths()),
        ),
    }
