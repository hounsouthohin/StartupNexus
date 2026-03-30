# agents/prebuild_pipeline.py
"""
Prebuild Truth Engine — Pipeline de vérification déterministe.

Exécute la toolchain native de la stack AVANT tout npm run build et produit un
PrebuildReport conforme à schemas/prebuild_report.schema.json.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# ── Identifiants des stages ──────────────────────────────────────────────────
STAGE_PRISMA_VALIDATE = "prisma_validate"
STAGE_PRISMA_GENERATE = "prisma_generate"
STAGE_TSC = "tsc"
STAGE_ESLINT = "eslint"
STAGE_AST_USE_CLIENT = "ast_use_client"      # Phase C
STAGE_DEP_CRUISER = "dependency_cruiser"     # Phase C

CRITICAL_STAGES = {STAGE_PRISMA_VALIDATE, STAGE_TSC, STAGE_ESLINT, STAGE_AST_USE_CLIENT}
PHASE_B_STAGES = [STAGE_PRISMA_VALIDATE, STAGE_PRISMA_GENERATE, STAGE_TSC, STAGE_ESLINT]
PHASE_C_STAGES = [STAGE_PRISMA_VALIDATE, STAGE_PRISMA_GENERATE, STAGE_TSC, STAGE_ESLINT, STAGE_AST_USE_CLIENT]

# Hooks React qui exigent "use client" comme premier statement AST
_REACT_HOOKS = frozenset({
    "useState", "useEffect", "useRef", "useCallback", "useMemo",
    "useReducer", "useContext", "useLayoutEffect", "useImperativeHandle",
    "useDebugValue", "useDeferredValue", "useTransition", "useId",
})

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "prebuild_report.schema.json"
_DEFAULT_STAGE_TIMEOUT_S = 120
_MAX_EVIDENCE_CHARS = 3000
_MAX_LLM_BUNDLE_CHARS = 2000

_TS_FIX_HINTS: dict[str, str] = {
    "TS7006": "Type explicitement le paramètre (ex: React.ChangeEvent<HTMLInputElement>).",
    "TS7031": "Ajoute un type explicite au destructuring (ex: { id }: { id: string }).",
    "TS2339": "Utilise uniquement des propriétés existantes dans le type/schema Prisma.",
    "TS2305": "Corrige l'import/export du symbole manquant dans le fichier indiqué.",
    "TS2345": "Aligne le type de l'argument avec le type attendu par la fonction.",
    "TS2552": "Ajoute l'import manquant (ex: NextResponse depuis next/server).",
}

_ESLINT_FIX_HINTS: dict[str, str] = {
    "no-restricted-imports": "Remplace l'import interdit par l'import stack autorisé.",
    "import/no-relative-packages": "Remplace l'import relatif inter-package par un alias/chemin autorisé.",
}


@dataclass
class Violation:
    rule_id: str
    file: str
    reason: str
    fix_hint: str
    line: int | None = None
    col: int | None = None


@dataclass
class StageResult:
    stage_id: str
    tool: str
    status: Literal["ok", "failed", "skipped", "error"]
    duration_ms: int
    violations: list[Violation] = field(default_factory=list)
    exit_code: int | None = None
    evidence: str = ""


@dataclass
class PrebuildReport:
    run_id: str
    project_name: str
    stack_id: str
    timestamp: str
    blocking: bool
    stages: list[StageResult]
    violations: list[Violation]
    llm_correction_bundle: str
    stages_passed: list[str]
    stages_failed: list[str]


def _truncate(text: str, n: int = _MAX_EVIDENCE_CHARS) -> str:
    text = str(text or "")
    return text if len(text) <= n else text[:n]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _relpath(path: str, root: str) -> str:
    p = str(path or "").strip().replace("\\", "/")
    if not p:
        return ""
    try:
        if os.path.isabs(p):
            p = os.path.relpath(p, root).replace("\\", "/")
    except Exception:
        pass
    return p


def _is_missing_tool_output(tool_name: str, output: str) -> bool:
    low = str(output or "").lower()
    markers = (
        "could not determine executable to run",
        "command not found",
        "is not recognized as an internal or external command",
        "npm err! enoent",
    )
    if any(m in low for m in markers):
        return True
    if tool_name == "eslint" and "no files matching the pattern" in low:
        return False
    return False


async def _run_subprocess(args: list[str], cwd: str, timeout_s: int = _DEFAULT_STAGE_TIMEOUT_S) -> subprocess.CompletedProcess:
    def _runner() -> subprocess.CompletedProcess:
        return subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=os.environ.copy(),
        )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _runner)


def format_llm_correction_bundle(violations: list[Violation]) -> str:
    if not violations:
        return ""

    lines = ["[PREBUILD_VIOLATIONS — corrections obligatoires avant build]"]
    for idx, v in enumerate(violations, start=1):
        where = v.file or "<unknown>"
        if v.line:
            where += f":{v.line}:{v.col or 1}"
        reason = " ".join(str(v.reason or "").split())
        hint = " ".join(str(v.fix_hint or "").split())
        lines.append(f"{idx}. {where} — règle: {v.rule_id}")
        lines.append(f"   {reason}")
        lines.append(f"   Fix: {hint}")

    payload = "\n".join(lines)
    if len(payload) > _MAX_LLM_BUNDLE_CHARS:
        payload = payload[: _MAX_LLM_BUNDLE_CHARS - 32] + "\n...[bundle tronqué]..."
    return payload


def report_to_dict(report: PrebuildReport) -> dict:
    return {
        "run_id": report.run_id,
        "project_name": report.project_name,
        "stack_id": report.stack_id,
        "timestamp": report.timestamp,
        "blocking": report.blocking,
        "stages": [
            {
                "stage_id": s.stage_id,
                "tool": s.tool,
                "status": s.status,
                "duration_ms": s.duration_ms,
                "exit_code": s.exit_code,
                "evidence": _truncate(s.evidence),
                "violations": [
                    {
                        "rule_id": v.rule_id,
                        "file": v.file,
                        "line": v.line,
                        "col": v.col,
                        "reason": v.reason,
                        "fix_hint": v.fix_hint,
                    }
                    for v in s.violations
                ],
            }
            for s in report.stages
        ],
        "violations": [
            {
                "rule_id": v.rule_id,
                "file": v.file,
                "line": v.line,
                "col": v.col,
                "reason": v.reason,
                "fix_hint": v.fix_hint,
            }
            for v in report.violations
        ],
        "llm_correction_bundle": report.llm_correction_bundle,
        "stages_passed": report.stages_passed,
        "stages_failed": report.stages_failed,
    }


def _validate_schema(data: dict) -> None:
    try:
        from jsonschema import validate
    except ModuleNotFoundError:
        return
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    validate(instance=data, schema=schema)


def report_from_dict(data: dict) -> PrebuildReport:
    if not isinstance(data, dict):
        raise ValueError("prebuild_report doit être un objet JSON.")
    _validate_schema(data)

    stages: list[StageResult] = []
    for raw in data.get("stages", []):
        violations = [
            Violation(
                rule_id=str(v.get("rule_id", "")),
                file=str(v.get("file", "")),
                reason=str(v.get("reason", "")),
                fix_hint=str(v.get("fix_hint", "")),
                line=v.get("line"),
                col=v.get("col"),
            )
            for v in (raw.get("violations") or [])
        ]
        stages.append(
            StageResult(
                stage_id=str(raw.get("stage_id", "")),
                tool=str(raw.get("tool", "")),
                status=str(raw.get("status", "error")),  # type: ignore[arg-type]
                duration_ms=int(raw.get("duration_ms", 0)),
                exit_code=raw.get("exit_code"),
                evidence=str(raw.get("evidence", "")),
                violations=violations,
            )
        )

    violations_all = [
        Violation(
            rule_id=str(v.get("rule_id", "")),
            file=str(v.get("file", "")),
            reason=str(v.get("reason", "")),
            fix_hint=str(v.get("fix_hint", "")),
            line=v.get("line"),
            col=v.get("col"),
        )
        for v in (data.get("violations") or [])
    ]

    return PrebuildReport(
        run_id=str(data.get("run_id", "")),
        project_name=str(data.get("project_name", "")),
        stack_id=str(data.get("stack_id", "")),
        timestamp=str(data.get("timestamp", "")),
        blocking=bool(data.get("blocking", False)),
        stages=stages,
        violations=violations_all,
        llm_correction_bundle=str(data.get("llm_correction_bundle", "")),
        stages_passed=[str(x) for x in (data.get("stages_passed") or [])],
        stages_failed=[str(x) for x in (data.get("stages_failed") or [])],
    )


def _dedupe_violations(violations: list[Violation]) -> list[Violation]:
    seen: set[tuple] = set()
    result: list[Violation] = []
    for v in violations:
        key = (v.rule_id, v.file, v.line, v.col, v.reason, v.fix_hint)
        if key in seen:
            continue
        seen.add(key)
        result.append(v)
    return result


async def _run_prisma_validate(project_dir: str) -> StageResult:
    started = time.perf_counter()
    tool = "npx prisma validate --schema prisma/schema.prisma"
    schema_path = os.path.join(project_dir, "prisma", "schema.prisma")

    if shutil.which("npx") is None:
        return StageResult(STAGE_PRISMA_VALIDATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="npx introuvable")
    if not os.path.exists(schema_path):
        return StageResult(STAGE_PRISMA_VALIDATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="schema.prisma absent")

    try:
        res = await _run_subprocess(["npx", "prisma", "validate", "--schema", "prisma/schema.prisma"], cwd=project_dir)
        output = _truncate((res.stdout or "") + "\n" + (res.stderr or ""))
        if res.returncode == 0:
            return StageResult(STAGE_PRISMA_VALIDATE, tool, "ok", int((time.perf_counter() - started) * 1000), exit_code=0, evidence=output)
        if _is_missing_tool_output("prisma", output):
            return StageResult(STAGE_PRISMA_VALIDATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence=output)

        violation = Violation(
            rule_id="prisma_schema_invalid",
            file="prisma/schema.prisma",
            reason=output.splitlines()[-1][:500] if output else "Schema Prisma invalide",
            fix_hint="Corrige prisma/schema.prisma (relations, types, attributs) puis relance prisma validate.",
        )
        return StageResult(STAGE_PRISMA_VALIDATE, tool, "failed", int((time.perf_counter() - started) * 1000), violations=[violation], exit_code=res.returncode, evidence=output)
    except subprocess.TimeoutExpired:
        return StageResult(STAGE_PRISMA_VALIDATE, tool, "error", int((time.perf_counter() - started) * 1000), evidence="timeout prisma validate >120s")
    except Exception as e:
        return StageResult(STAGE_PRISMA_VALIDATE, tool, "error", int((time.perf_counter() - started) * 1000), evidence=_truncate(str(e)))


async def _run_prisma_generate(project_dir: str) -> StageResult:
    started = time.perf_counter()
    tool = "npx prisma generate --schema prisma/schema.prisma"
    schema_path = os.path.join(project_dir, "prisma", "schema.prisma")

    if shutil.which("npx") is None:
        return StageResult(STAGE_PRISMA_GENERATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="npx introuvable")
    if not os.path.exists(schema_path):
        return StageResult(STAGE_PRISMA_GENERATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="schema.prisma absent")

    try:
        res = await _run_subprocess(["npx", "prisma", "generate", "--schema", "prisma/schema.prisma"], cwd=project_dir)
        output = _truncate((res.stdout or "") + "\n" + (res.stderr or ""))
        if res.returncode == 0:
            return StageResult(STAGE_PRISMA_GENERATE, tool, "ok", int((time.perf_counter() - started) * 1000), exit_code=0, evidence=output)
        if _is_missing_tool_output("prisma", output):
            return StageResult(STAGE_PRISMA_GENERATE, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence=output)
        logger.warning("[prebuild][prisma_generate] non bloquant: exit=%s", res.returncode)
        return StageResult(STAGE_PRISMA_GENERATE, tool, "error", int((time.perf_counter() - started) * 1000), exit_code=res.returncode, evidence=output)
    except subprocess.TimeoutExpired:
        return StageResult(STAGE_PRISMA_GENERATE, tool, "error", int((time.perf_counter() - started) * 1000), evidence="timeout prisma generate >120s")
    except Exception as e:
        return StageResult(STAGE_PRISMA_GENERATE, tool, "error", int((time.perf_counter() - started) * 1000), evidence=_truncate(str(e)))


async def _run_tsc(project_dir: str) -> StageResult:
    started = time.perf_counter()
    tool = "npx tsc --noEmit --pretty false"
    tsconfig = os.path.join(project_dir, "tsconfig.json")

    if shutil.which("npx") is None:
        return StageResult(STAGE_TSC, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="npx introuvable")
    if not os.path.exists(tsconfig):
        return StageResult(STAGE_TSC, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="tsconfig absent")

    try:
        res = await _run_subprocess(["npx", "tsc", "--noEmit", "--pretty", "false"], cwd=project_dir)
        output = _truncate((res.stdout or "") + "\n" + (res.stderr or ""))
        if _is_missing_tool_output("tsc", output):
            return StageResult(STAGE_TSC, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence=output)

        violations: list[Violation] = []
        rgx = re.compile(r"^(?P<file>.+?)\((?P<line>\d+),(?P<col>\d+)\):\s*error\s+(?P<code>TS\d+):\s*(?P<msg>.+)$")
        for raw in output.splitlines():
            m = rgx.match(raw.strip())
            if not m:
                continue
            code = m.group("code")
            msg = m.group("msg").strip()
            file_rel = _relpath(m.group("file"), project_dir)
            violations.append(
                Violation(
                    rule_id=code,
                    file=file_rel,
                    line=int(m.group("line")),
                    col=int(m.group("col")),
                    reason=f"{code}: {msg}",
                    fix_hint=_TS_FIX_HINTS.get(code, "Corrige l'erreur TypeScript sur la ligne indiquée puis relance tsc."),
                )
            )

        if res.returncode == 0 and not violations:
            return StageResult(STAGE_TSC, tool, "ok", int((time.perf_counter() - started) * 1000), exit_code=0, evidence=output)

        if not violations:
            violations = [
                Violation(
                    rule_id="TS_UNKNOWN",
                    file="",
                    reason="tsc a échoué sans ligne parseable.",
                    fix_hint="Lis la sortie tsc complète et corrige la première erreur bloquante.",
                )
            ]
        return StageResult(STAGE_TSC, tool, "failed", int((time.perf_counter() - started) * 1000), violations=violations, exit_code=res.returncode, evidence=output)
    except subprocess.TimeoutExpired:
        return StageResult(STAGE_TSC, tool, "error", int((time.perf_counter() - started) * 1000), evidence="timeout tsc >120s")
    except Exception as e:
        return StageResult(STAGE_TSC, tool, "error", int((time.perf_counter() - started) * 1000), evidence=_truncate(str(e)))


async def _run_eslint(project_dir: str, eslint_config: str | None = None) -> StageResult:
    started = time.perf_counter()
    tool = "npx eslint app lib middleware.ts prisma.config.ts --ext .ts,.tsx --format json"

    if shutil.which("npx") is None:
        return StageResult(STAGE_ESLINT, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="npx introuvable")

    config_path = eslint_config or os.path.join(project_dir, ".eslintrc.stack.json")
    if not os.path.exists(config_path):
        return StageResult(STAGE_ESLINT, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence="config eslint absente")

    target_candidates = ["app", "lib", "middleware.ts", "prisma.config.ts"]
    targets = [t for t in target_candidates if os.path.exists(os.path.join(project_dir, t))]
    if not targets:
        return StageResult(
            STAGE_ESLINT,
            tool,
            "skipped",
            int((time.perf_counter() - started) * 1000),
            evidence="aucune cible eslint détectée",
        )

    # --resolve-plugins-relative-to . force ESLint 8 à chercher les plugins dans
    # node_modules/ du workdir projet, même quand --config reçoit un chemin absolu.
    # Sans ce flag, ESLint cherche les plugins relativement au répertoire de la config
    # (qui peut être le répertoire d'installation de npx, pas le projet).
    args = [
        "npx",
        "eslint",
        *targets,
        "--ext",
        ".ts,.tsx",
        "--format",
        "json",
        "--config",
        config_path,
        "--resolve-plugins-relative-to",
        ".",
    ]
    try:
        res = await _run_subprocess(args, cwd=project_dir)
        stdout = (res.stdout or "").strip()
        stderr = (res.stderr or "").strip()
        output = _truncate(stdout + ("\n" + stderr if stderr else ""))
        if _is_missing_tool_output("eslint", output):
            return StageResult(STAGE_ESLINT, tool, "skipped", int((time.perf_counter() - started) * 1000), evidence=output)

        violations: list[Violation] = []
        data = []
        if stdout:
            try:
                loaded = json.loads(stdout)
                if isinstance(loaded, list):
                    data = loaded
            except json.JSONDecodeError:
                data = []

        for entry in data:
            file_path = _relpath(str(entry.get("filePath", "")), project_dir)
            for msg in entry.get("messages", []) or []:
                if int(msg.get("severity", 0) or 0) < 2:
                    continue
                rule_id = str(msg.get("ruleId") or "eslint_error")
                reason = str(msg.get("message") or "").strip()
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        file=file_path,
                        line=int(msg.get("line") or 0) or None,
                        col=int(msg.get("column") or 0) or None,
                        reason=reason,
                        fix_hint=_ESLINT_FIX_HINTS.get(rule_id, "Corrige la règle ESLint signalée puis relance eslint."),
                    )
                )

        if res.returncode == 0 and not violations:
            return StageResult(STAGE_ESLINT, tool, "ok", int((time.perf_counter() - started) * 1000), exit_code=0, evidence=output)

        if not violations:
            violations = [
                Violation(
                    rule_id="eslint_error",
                    file="",
                    reason=_truncate(stderr or "eslint a échoué sans JSON parseable."),
                    fix_hint="Corrige la première erreur ESLint bloquante puis relance eslint.",
                )
            ]
        return StageResult(STAGE_ESLINT, tool, "failed", int((time.perf_counter() - started) * 1000), violations=violations, exit_code=res.returncode, evidence=output)
    except subprocess.TimeoutExpired:
        return StageResult(STAGE_ESLINT, tool, "error", int((time.perf_counter() - started) * 1000), evidence="timeout eslint >120s")
    except Exception as e:
        return StageResult(STAGE_ESLINT, tool, "error", int((time.perf_counter() - started) * 1000), evidence=_truncate(str(e)))


async def run_prebuild_pipeline(
    project_dir: str,
    stack_id: str,
    run_id: str,
    project_name: str,
    stages: list[str] | None = None,
) -> PrebuildReport:
    selected = stages or list(PHASE_B_STAGES)
    runners = {
        STAGE_PRISMA_VALIDATE: _run_prisma_validate,
        STAGE_PRISMA_GENERATE: _run_prisma_generate,
        STAGE_TSC: _run_tsc,
        STAGE_ESLINT: _run_eslint,
        STAGE_AST_USE_CLIENT: _run_ast_use_client,
    }

    stage_results: list[StageResult] = []
    for stage_id in selected:
        runner = runners.get(stage_id)
        if runner is None:
            stage_results.append(
                StageResult(
                    stage_id=stage_id,
                    tool="",
                    status="skipped",
                    duration_ms=0,
                    evidence=f"stage non implémenté: {stage_id}",
                )
            )
            continue
        try:
            result = await runner(project_dir)  # type: ignore[misc]
            if not isinstance(result, StageResult):
                # Stub non implémenté (retourne None/...) → skipped non bloquant
                stage_results.append(StageResult(stage_id=stage_id, tool="", status="skipped", duration_ms=0, evidence="stage stub non implémenté"))
                continue
        except Exception as _stage_err:
            logger.warning("[prebuild][%s] exception inattendue: %s", stage_id, _stage_err)
            stage_results.append(StageResult(stage_id=stage_id, tool="", status="error", duration_ms=0, evidence=_truncate(str(_stage_err))))
            continue
        stage_results.append(result)

    all_violations = _dedupe_violations([v for s in stage_results for v in s.violations])
    blocking = any(s.stage_id in CRITICAL_STAGES and s.status == "failed" for s in stage_results)
    stages_passed = [s.stage_id for s in stage_results if s.status == "ok"]
    stages_failed = [s.stage_id for s in stage_results if s.status in ("failed", "error")]

    blocking_violations = [v for s in stage_results if s.status == "failed" for v in s.violations]
    llm_bundle = format_llm_correction_bundle(_dedupe_violations(blocking_violations)) if blocking else ""

    report = PrebuildReport(
        run_id=run_id,
        project_name=project_name,
        stack_id=stack_id,
        timestamp=_now_iso(),
        blocking=blocking,
        stages=stage_results,
        violations=all_violations,
        llm_correction_bundle=llm_bundle,
        stages_passed=stages_passed,
        stages_failed=stages_failed,
    )

    report_dict = report_to_dict(report)
    try:
        _validate_schema(report_dict)
    except Exception as e:
        logger.error("[prebuild] report invalide au schéma: %s", e)

    try:
        out_path = os.path.join(project_dir, "prebuild_report.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, ensure_ascii=False, indent=2)
        logger.info(
            "[prebuild] report écrit: %s | blocking=%s | stages_failed=%s",
            out_path,
            blocking,
            stages_failed,
        )
    except Exception as e:
        logger.warning("[prebuild] écriture report non bloquante: %s", e)

    return report


async def _run_ast_use_client(project_dir: str) -> StageResult:
    """
    Stage ast_use_client — détecte les fichiers qui importent des hooks React
    sans directive 'use client' comme PREMIER statement AST.

    CONTRAT D'IMPLÉMENTATION POUR CODEX :

    Outil requis : tree-sitter-typescript (pip install tree-sitter tree-sitter-typescript)
    Cible : fichiers app/**/*.tsx et app/**/*.ts uniquement
            (exclus : app/api/**, app/layout.tsx, les Server Components légitimes)

    Algorithme attendu :
      Pour chaque fichier .tsx dans app/ (hors app/api/, app/layout.tsx) :
        1. Parser l'AST avec tree-sitter-typescript (parser error-tolerant)
        2. Détecter si au moins un hook de _REACT_HOOKS est importé OU appelé
        3. Si oui → vérifier que le PREMIER statement AST est ExpressionStatement
           dont la valeur est StringLiteral 'use client'
        4. Si le premier statement n'est pas 'use client' → Violation

    Règles de faux positifs à éviter :
      - app/layout.tsx : SKIP toujours (Server Component valide avec ClerkProvider)
      - app/api/** : SKIP toujours (Route Handlers — pas de hooks côté serveur)
      - Fichiers sans import de hook et sans appel de hook → SKIP
      - Server Components légitimes : si aucun hook détecté → pas de violation

    Succès (status=ok)   : aucune violation
    Échec (status=failed): au moins un fichier avec hook sans 'use client'
    Absent (status=skipped): tree-sitter ou tree-sitter-typescript absent (shutil.which ou import)
    Erreur (status=error): exception Python non récupérable (non bloquant pour les fichiers non parsés)

    Violations produites :
        rule_id  = "use_client"
        file     = chemin relatif (ex: app/new/page.tsx)
        line     = None (la directive doit être ligne 1 absolue)
        col      = None
        reason   = "Hooks React détectés ({hooks}) sans directive 'use client' en première ligne."
        fix_hint = "Ajouter '\"use client\"' en toute première ligne de {file}, avant tous les imports."

    Note : PHASE_C_STAGES = [prisma_validate, prisma_generate, tsc, eslint, ast_use_client]
    Pour activer ce stage, passer stages=PHASE_C_STAGES à run_prebuild_pipeline().
    Le câblage dans dev_graph.py doit passer PHASE_C_STAGES une fois ce stage implémenté.
    """
    started = time.perf_counter()
    tool = "tree-sitter-typescript (ast use_client)"

    def _node_text(node, src: bytes) -> str:
        try:
            return src[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _iter_target_files(root_dir: str) -> list[tuple[str, str]]:
        app_root = Path(root_dir) / "app"
        if not app_root.exists():
            return []
        out: list[tuple[str, str]] = []
        for p in app_root.rglob("*.tsx"):
            rel = p.relative_to(root_dir).as_posix()
            if rel.startswith("app/api/"):
                continue
            if rel == "app/layout.tsx":
                continue
            out.append((str(p), rel))
        return out

    def _build_parser():
        try:
            from tree_sitter import Language, Parser  # type: ignore
            import tree_sitter_typescript as ts_lang  # type: ignore
        except Exception as imp_err:
            return None, f"tree-sitter indisponible: {imp_err}"

        lang_candidate = None
        for attr in ("language_tsx", "tsx", "LANGUAGE_TSX", "TSX_LANGUAGE"):
            if not hasattr(ts_lang, attr):
                continue
            cand = getattr(ts_lang, attr)
            try:
                lang_candidate = cand() if callable(cand) else cand
            except Exception:
                lang_candidate = cand
            if lang_candidate is not None:
                break

        if lang_candidate is None:
            return None, "language TSX introuvable dans tree_sitter_typescript"

        try:
            if isinstance(lang_candidate, Language):
                language = lang_candidate
            else:
                language = Language(lang_candidate)
        except Exception:
            language = lang_candidate

        try:
            parser = Parser(language)
        except Exception:
            parser = Parser()
            try:
                parser.set_language(language)
            except Exception:
                parser.language = language
        return parser, ""

    def _detect_hooks(root_node, src: bytes) -> list[str]:
        detected: set[str] = set()
        stack = [root_node]
        while stack:
            node = stack.pop()
            ntype = getattr(node, "type", "")

            if ntype == "import_statement":
                stmt = _node_text(node, src)
                if "from 'react'" in stmt or 'from "react"' in stmt:
                    for hook in _REACT_HOOKS:
                        if re.search(rf"\b{re.escape(hook)}\b", stmt):
                            detected.add(hook)
            elif ntype == "call_expression":
                expr = _node_text(node, src)
                for hook in _REACT_HOOKS:
                    if re.search(rf"(?<![\w$])(?:React\.)?{re.escape(hook)}\s*\(", expr):
                        detected.add(hook)

            children = getattr(node, "children", None) or []
            if children:
                stack.extend(children)

        return sorted(detected)

    def _first_statement_is_use_client(root_node, src: bytes) -> bool:
        for child in (getattr(root_node, "named_children", None) or []):
            stmt = _node_text(child, src).strip()
            if not stmt:
                continue
            return bool(re.match(r"^(?:'use client'|\"use client\");?$", stmt))
        return False

    # Modules server-only incompatibles avec un Client Component.
    # Next.js refuse un bundle client qui importe ces paths.
    _SERVER_ONLY_IMPORTS = (
        "@clerk/nextjs/server",
        "server-only",
        "next/headers",
        "next/cookies",
    )

    def _has_server_only_imports(root_node, src: bytes) -> list[str]:
        """Retourne la liste des imports server-only trouvés dans le fichier."""
        found: list[str] = []
        stack = [root_node]
        while stack:
            node = stack.pop()
            if getattr(node, "type", "") == "import_statement":
                stmt = _node_text(node, src)
                for pkg in _SERVER_ONLY_IMPORTS:
                    if f"'{pkg}'" in stmt or f'"{pkg}"' in stmt:
                        found.append(pkg)
            children = getattr(node, "children", None) or []
            if children:
                stack.extend(children)
        return found

    parser, parser_reason = _build_parser()
    if parser is None:
        return StageResult(
            STAGE_AST_USE_CLIENT,
            tool,
            "skipped",
            int((time.perf_counter() - started) * 1000),
            evidence=parser_reason or "parser indisponible",
        )

    targets = _iter_target_files(project_dir)
    if not targets:
        return StageResult(
            STAGE_AST_USE_CLIENT,
            tool,
            "ok",
            int((time.perf_counter() - started) * 1000),
            evidence="aucun fichier cible app/**/*.tsx",
        )

    violations: list[Violation] = []
    parse_errors: list[str] = []
    hooks_seen = 0

    for abs_path, rel_path in targets:
        try:
            src = Path(abs_path).read_bytes()
            tree = parser.parse(src)
            root = tree.root_node
            has_use_client = _first_statement_is_use_client(root, src)
            hooks = _detect_hooks(root, src)

            # Check 1 — hooks sans "use client"
            if hooks:
                hooks_seen += 1
                if not has_use_client:
                    hooks_str = ", ".join(hooks[:8])
                    violations.append(
                        Violation(
                            rule_id="use_client",
                            file=rel_path,
                            line=None,
                            col=None,
                            reason=f"Hooks React détectés ({hooks_str}) sans directive 'use client' en première ligne.",
                            fix_hint=f"Ajouter '\"use client\"' en toute première ligne de {rel_path}, avant tous les imports.",
                        )
                    )

            # Check 2 — "use client" avec imports server-only (boundary violation)
            if has_use_client:
                server_imports = _has_server_only_imports(root, src)
                if server_imports:
                    pkgs = ", ".join(server_imports[:4])
                    violations.append(
                        Violation(
                            rule_id="client_server_boundary",
                            file=rel_path,
                            line=None,
                            col=None,
                            reason=(
                                f"{rel_path} est un Client Component ('use client') "
                                f"mais importe des modules server-only : {pkgs}."
                            ),
                            fix_hint=(
                                f"Dans {rel_path}, retire les imports {pkgs}. "
                                "Pour l'auth dans un Client Component, utilise "
                                "`useAuth()` ou `useUser()` depuis '@clerk/nextjs' "
                                "(jamais '@clerk/nextjs/server')."
                            ),
                        )
                    )
        except Exception as file_err:
            parse_errors.append(f"{rel_path}: {str(file_err)[:120]}")

    if violations:
        use_client_count = sum(1 for v in violations if v.rule_id == "use_client")
        boundary_count = sum(1 for v in violations if v.rule_id == "client_server_boundary")
        evidence_parts = []
        if use_client_count:
            evidence_parts.append(f"{use_client_count} use_client manquant(s)")
        if boundary_count:
            evidence_parts.append(f"{boundary_count} client_server_boundary")
        evidence = (
            f"{len(violations)} violation(s) AST [{', '.join(evidence_parts)}] "
            f"sur {len(targets)} fichiers cibles (fichiers avec hooks={hooks_seen})"
        )
        return StageResult(
            STAGE_AST_USE_CLIENT,
            tool,
            "failed",
            int((time.perf_counter() - started) * 1000),
            violations=violations,
            evidence=evidence,
        )

    if parse_errors:
        evidence = _truncate(
            "parse_errors: " + " | ".join(parse_errors[:5])
        )
        return StageResult(
            STAGE_AST_USE_CLIENT,
            tool,
            "error",
            int((time.perf_counter() - started) * 1000),
            evidence=evidence,
        )

    return StageResult(
        STAGE_AST_USE_CLIENT,
        tool,
        "ok",
        int((time.perf_counter() - started) * 1000),
        evidence=f"ok — {len(targets)} fichiers cibles, hooks_detected={hooks_seen}",
    )
