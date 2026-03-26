# Phase 1 - Module Inventory

## New modules introduced during C3 extraction

1. `factory-sprint0/agents/dev_compat.py`
- Purpose: isolate fallback compatibility shims for `ChatOpenAI`, LangChain messages, and `LLMConversationRunner`.
- Why: keep `dev.py` compact while preserving import safety in lightweight test environments.

2. `factory-sprint0/agents/dev_file_ops.py`
- Purpose: isolate file-system orchestration helpers (`clean_project_workdir`, `write_template_files`).
- Why: keep `dev.py` focused on orchestration and reduce file length (< 400 lines target).

## Active ownership after extraction

1. `factory-sprint0/agents/dev.py`
- Thin orchestrator: setup/config/init, call to `run_dev_loop`, metadata packaging.

2. `factory-sprint0/agents/dev_loop.py`
- Main generation + supervision + gating + reflection + terminal guard loop.
