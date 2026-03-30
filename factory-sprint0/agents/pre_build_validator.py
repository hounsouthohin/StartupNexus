"""
pre_build_validator.py — Validation pré-build de l'état des fichiers générés.

DEPRECATED (Phase A - Prebuild Truth Engine, 2026-03-30).
Legacy module kept for rollback/tests only.
Active runtime uses agents.dev_graph via dev_test_activity.

Extraite de dev.py (inner function _prebuild_gates + _find_content_guard_violations
+ _collect_blocking_content_guard_targets) pour réduire la taille de dev_agent().

PreBuildValidator regroupe tous les checks qui doivent passer avant qu'un run_build()
soit autorisé :
  0. Supervision loop — corrections superviseurs en attente
  1. Blueprint Validator — fichiers obligatoires présents
  2. Path Guards — conventions de nommage (App Router)
  3. Forbidden Paths — pages/ interdit
  4. Forbidden Imports — tokens interdits dans le code
  5. Content Guards — règles regex/AST config-driven
"""

from __future__ import annotations

import logging
import re
import shutil as _shutil
from pathlib import PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .file_supervision_loop import FileSupervisionLoop

from .dev_path_utils import first_directive_line, collect_forbidden_import_violations
from .stack_config import get_forbidden_imports, get_forbidden_paths

logger = logging.getLogger(__name__)
logger.warning(
    "[DEPRECATED] agents.pre_build_validator is legacy and not used by active runtime path "
    "(dev_test_activity -> dev_graph)."
)


class PreBuildValidator:
    """
    Valide les préconditions du build pour un ensemble de fichiers générés.

    Instancier une fois dans dev_agent() avec la config de la run.
    Appeler check(files_dict) avant chaque run_build().
    """

    def __init__(
        self,
        stack_cfg: dict,
        required_files: list[str],
        templated_names: set[str],
        supervision_loop: "FileSupervisionLoop",
        scaffold_extends_paths: set[str],
        stack_id: str,
        guard_warning_hits: dict,
    ) -> None:
        self.stack_cfg = stack_cfg
        self.required_files = required_files
        self.templated_names = templated_names
        self.supervision_loop = supervision_loop
        self.scaffold_extends_paths = scaffold_extends_paths
        self.stack_id = stack_id
        self.guard_warning_hits = guard_warning_hits

    # ── API publique ─────────────────────────────────────────────────────────

    def check(self, files_dict: dict, bypass_supervision: bool = False) -> tuple[bool, str, str, list]:
        """
        Lance tous les checks pré-build dans l'ordre de priorité.
        Retourne (blocked, message, guard_id, warnings).
        Si blocked=False → run_build autorisé.
        bypass_supervision=True : ignore le gate supervision (best-effort après stagnation).
        """
        warnings: list[str] = []

        # 0. Supervision loop
        if not bypass_supervision and self.supervision_loop.has_pending_corrections():
            pending = self.supervision_loop.pending_paths()
            return True, (
                "SUPERVISION — BUILD BLOQUÉ\n"
                f"{len(pending)} fichier(s) ont des corrections superviseurs en attente :\n"
                + "\n".join(f"  - {p}" for p in pending)
                + "\nCorrige ces fichiers avec write_file() avant d'appeler run_build()."
            ), "supervision_pending", []

        # 1. Blueprint Validator
        present = set(files_dict.keys()) | self.templated_names
        present_norm = {p.replace("\\", "/").lower() for p in present}
        missing = [
            f for f in self.required_files
            if not any(
                pp == str(f).replace("\\", "/").lower()
                or pp.endswith("/" + str(f).replace("\\", "/").lower())
                for pp in present_norm
            )
        ]
        if missing:
            return True, (
                "BLUEPRINT VALIDATOR — BUILD BLOQUÉ\n"
                f"{len(missing)} fichier(s) obligatoire(s) manquant(s) :\n"
                + "\n".join(f"  - {f}" for f in missing)
                + "\n\nGénère ces fichiers avec write_file() maintenant."
                " run_build sera disponible une fois tous présents."
            ), "blueprint", warnings

        # 2. Path Guards
        blocked, msg, guard_id, pg_warnings = self._check_path_guards(files_dict)
        warnings.extend(pg_warnings)
        if blocked:
            return True, msg, guard_id, warnings

        # 3. Forbidden Paths
        forbidden = get_forbidden_paths(self.stack_id) if self.stack_id else ["pages/", "src/pages/"]
        forbidden_violations = [
            fp.replace("\\", "/")
            for fp in files_dict.keys()
            if any(fp.replace("\\", "/").startswith(f) for f in forbidden)
        ]
        if forbidden_violations:
            return True, (
                "FORBIDDEN PATHS GUARD — BUILD BLOQUÉ\n"
                "Fichiers détectés dans un chemin interdit (Pages Router au lieu de App Router) :\n"
                + "\n".join(f"  - {f}" for f in forbidden_violations)
                + "\n\nCORRECTION OBLIGATOIRE — App Router UNIQUEMENT :\n"
                "INTERDIT: pages/api/<resource>/index.ts  →  CORRECT: app/api/<resource>/route.ts\n"
                "INTERDIT: pages/api/<resource>/[id].ts  →  CORRECT: app/api/<resource>/[id]/route.ts\n"
                "Structure App Router API :\n"
                "  app/api/<resource>/route.ts            → export async function GET() / POST()\n"
                "  app/api/<resource>/[id]/route.ts       → export async function GET() / PUT() / DELETE()\n"
                "Crée les fichiers App Router corrects avec write_file(), puis rappelle run_build."
            ), "forbidden_paths", warnings

        # 4. Forbidden Imports
        forbidden_tokens = get_forbidden_imports(self.stack_id) if self.stack_id else []
        import_violations = collect_forbidden_import_violations(
            files_dict, forbidden_tokens, templated_names=self.templated_names
        )
        if import_violations:
            details = "\n".join(f"  - {fp}  (token: {tok})" for fp, tok in import_violations)
            warn_msg = (
                "FORBIDDEN IMPORTS WARNING — NON BLOQUANT\n"
                "Des imports/patterns interdits par la stack ont été détectés :\n"
                f"{details}\n\n"
                "Corrige les imports selon les règles stack (auth/ORM/UI), puis rappelle run_build."
            )
            logger.warning(f"[PREBUILD WARN forbidden_imports] {len(import_violations)} violation(s)")
            warnings.append(f"[PREBUILD WARNING:forbidden_imports]\n{warn_msg}")

        # 5. AST Guards (stub P3)
        for guard in self.stack_cfg.get("content_guards", []):
            gid = guard.get("id", "unknown")
            engine = str(guard.get("engine", "regex")).strip().lower()
            if engine != "ast":
                continue
            ast_tool = guard.get("ast_tool", "ts-morph")
            tool_binary = "node" if ast_tool == "ts-morph" else "semgrep"
            if _shutil.which(tool_binary) is None:
                logger.warning(
                    f"[AST_GUARD {gid}] {ast_tool} non disponible "
                    f"('{tool_binary}' introuvable dans PATH) — guard skippé."
                )
                warnings.append(f"[AST_GUARD SKIPPED:{gid}] {ast_tool} non disponible")
            else:
                logger.info(f"[AST_GUARD {gid}] {ast_tool} disponible — exécution à implémenter (P3)")
                warnings.append(f"[AST_GUARD TODO:{gid}] subprocess {ast_tool} non encore câblé")

        # 5b. Content Guards (regex)
        for gid, mode, msg_lines, violations in self._find_content_guard_violations(files_dict):
            if not violations:
                continue
            details = "\n".join(
                f"  - {fp}  [{', '.join(found)}]" for fp, found in violations
            )
            msg = "\n".join(msg_lines).replace("{details}", details)
            if mode == "warn":
                self.guard_warning_hits[gid] = self.guard_warning_hits.get(gid, 0) + len(violations)
                logger.warning(f"[CONTENT_GUARD WARN {gid}] {len(violations)} violation(s) — non bloquant")
                warnings.append(f"[CONTENT_GUARD WARNING:{gid}]\n{msg}")
            else:
                return True, msg, gid, warnings

        return False, "", "", warnings

    def find_blocking_targets(self, files_dict: dict) -> tuple[str, list[str]]:
        """
        Retourne (guard_id, paths) du premier content_guard bloquant en violation.
        Sans side-effects — utilisé par _build_run_state pour le blocker actif.
        """
        for gid, _mode, _msg_lines, violations in self._find_content_guard_violations(
            files_dict, mode_filter="block"
        ):
            violating_paths = [fp for fp, _found in violations]
            if violating_paths:
                return gid, violating_paths
        return "", []

    # ── Helpers privés ───────────────────────────────────────────────────────

    def _check_path_guards(self, files_dict: dict) -> tuple[bool, str, str, list]:
        warnings: list[str] = []
        for pg in self.stack_cfg.get("path_guards", []):
            pg_id = str(pg.get("id", "unknown"))
            pg_kind = str(pg.get("kind", "")).strip()
            pg_mode = str(pg.get("mode", "warn")).strip().lower()
            if pg_mode not in ("warn", "block"):
                pg_mode = "warn"
            pg_msg_lines = pg.get("message_lines", [f"{pg_id} PATH GUARD", "{details}"])

            violations: list[tuple[str, str]] = []

            if pg_kind == "app_router_convention":
                root = str(pg.get("route_root", "app/"))
                exts = tuple(pg.get("file_extensions", [".tsx"]))
                valid_route_names = set(pg.get("valid_route_names", [
                    "layout", "page", "error", "loading", "not-found", "template", "default"
                ]))
                excluded_dirs = set(pg.get("excluded_directories", [
                    "components", "lib", "utils", "hooks", "styles", "types",
                    "context", "providers", "helpers"
                ]))
                for fp in files_dict.keys():
                    p = PurePosixPath(fp.replace("\\", "/"))
                    fp_norm = str(p)
                    if not fp_norm.startswith(root):
                        continue
                    if p.suffix not in exts:
                        continue
                    if len(p.parts) >= 3 and p.parts[1] in excluded_dirs:
                        continue
                    if p.stem in valid_route_names:
                        continue
                    suggested = str(p.parent / p.stem / "page.tsx")
                    violations.append((fp_norm, suggested))

            elif pg_kind == "app_router_api_naming":
                api_root = str(pg.get("api_root", "app/api/"))
                exts = tuple(pg.get("file_extensions", [".ts", ".tsx"]))
                valid_stem = str(pg.get("api_valid_stem", "route"))
                for fp in files_dict.keys():
                    p = PurePosixPath(fp.replace("\\", "/"))
                    fp_norm = str(p)
                    if not fp_norm.startswith(api_root):
                        continue
                    if p.suffix not in exts:
                        continue
                    if p.stem == valid_stem:
                        continue
                    suggested = (
                        str(p.parent / "route.ts") if p.stem == "index"
                        else str(p.parent / p.stem / "route.ts")
                    )
                    violations.append((fp_norm, suggested))

            if violations:
                details = "\n".join(f"  - {fp}  →  {s}" for fp, s in violations)
                msg = "\n".join(pg_msg_lines).replace("{details}", details)
                if pg_mode == "warn":
                    self.guard_warning_hits[pg_id] = (
                        self.guard_warning_hits.get(pg_id, 0) + len(violations)
                    )
                    logger.warning(f"[PATH_GUARD WARN {pg_id}] {len(violations)} violation(s)")
                    warnings.append(f"[PATH_GUARD WARNING:{pg_id}]\n{msg}")
                else:
                    return True, msg, pg_id, warnings

        return False, "", "", warnings

    def _find_content_guard_violations(
        self, files_dict: dict, mode_filter: str | None = None
    ) -> list[tuple]:
        """
        Parcourt les content_guards (engine=regex uniquement) et retourne les violations.
        Retourne list of (guard_id, mode, msg_lines, violations).
        violations = list of (fp_norm, found_tokens).
        """
        results: list[tuple] = []
        for guard in self.stack_cfg.get("content_guards", []):
            gid = guard.get("id", "unknown")
            engine = str(guard.get("engine", "regex")).strip().lower()
            if engine == "ast":
                continue  # géré séparément dans check()
            mode = str(guard.get("mode", "block")).strip().lower()
            if mode not in ("block", "warn"):
                mode = "block"
            if mode_filter is not None and mode != mode_filter:
                continue

            file_prefix = guard.get("file_prefix", "")
            file_exts = guard.get("file_extensions", [])
            triggers = guard.get("trigger_contains", [])
            trigger_regexes = guard.get("trigger_regex", [])
            requires_contains_all = guard.get("requires_contains_all", []) or []
            requires_regex_all = guard.get("requires_regex_all", []) or []
            directive = guard.get("requires_first_directive")
            conflicts = guard.get("conflicts_with_directive")
            ignore_leading = bool(guard.get("ignore_leading_comments", False))
            exclude_paths = [str(p).replace("\\", "/") for p in (guard.get("exclude_paths", []) or [])]
            exclude_when = [str(s) for s in (guard.get("exclude_when_contains", []) or [])]
            msg_lines = guard.get("message_lines", [f"{gid} GUARD — BUILD BLOQUÉ", "{details}"])

            compiled_triggers: list[tuple[str, re.Pattern]] = []
            for rx in trigger_regexes:
                try:
                    compiled_triggers.append((str(rx), re.compile(str(rx), re.MULTILINE)))
                except re.error as e:
                    logger.warning(f"[CONTENT_GUARD {gid}] regex invalide ignorée: {rx} ({e})")
            compiled_required: list[tuple[str, re.Pattern]] = []
            for rx in requires_regex_all:
                try:
                    compiled_required.append((str(rx), re.compile(str(rx), re.MULTILINE)))
                except re.error as e:
                    logger.warning(f"[CONTENT_GUARD {gid}] requires_regex invalide ignorée: {rx} ({e})")

            violations: list[tuple[str, list]] = []
            for fp, fc in files_dict.items():
                fp_norm = fp.replace("\\", "/")
                if fp_norm in self.templated_names:
                    continue
                if any(fp_norm.startswith(xp) for xp in exclude_paths):
                    continue
                if file_prefix and not fp_norm.startswith(file_prefix):
                    continue
                if file_exts and not any(fp_norm.endswith(ext) for ext in file_exts):
                    continue
                if exclude_when and any(needle in fc for needle in exclude_when):
                    continue

                found = [t for t in triggers if t in fc]
                for rx_src, rx in compiled_triggers:
                    if rx.search(fc):
                        found.append(f"regex:{rx_src}")
                has_explicit = bool(triggers or compiled_triggers)
                if has_explicit and not found:
                    continue
                if not has_explicit:
                    found = ["scope"]

                missing_constraints = [n for n in requires_contains_all if n not in fc]
                for rx_src, rx in compiled_required:
                    if not rx.search(fc):
                        missing_constraints.append(f"regex:{rx_src}")
                if missing_constraints:
                    violations.append((fp_norm, found + [f"missing:{c}" for c in missing_constraints]))
                    continue
                if requires_contains_all or compiled_required:
                    continue  # all required conditions met

                if directive is not None or conflicts is not None:
                    first = first_directive_line(fc, ignore_leading_comments=ignore_leading)
                    first_norm = first.replace("'", "").replace('"', "").rstrip(";").strip()
                    if directive is not None and directive in first_norm:
                        continue
                    if conflicts is not None and conflicts not in first_norm:
                        continue

                violations.append((fp_norm, found))

            if violations:
                results.append((gid, mode, msg_lines, violations))

        return results
