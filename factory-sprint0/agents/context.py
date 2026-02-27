"""
Async-safe context variables for run_id and stack_id propagation.
Used across all agents and activities without shared mutable state.
"""
from contextvars import ContextVar

from agents.stack_config import _DEFAULT_STACK_ID

# --- Context variables ---
_run_id_ctx: ContextVar[str] = ContextVar("run_id", default="")
_stack_id_ctx: ContextVar[str] = ContextVar("stack_id", default=_DEFAULT_STACK_ID)


def set_run_id(run_id: str) -> None:
    _run_id_ctx.set(run_id or "")


def get_run_id() -> str:
    return _run_id_ctx.get()


def set_stack_id(stack_id: str) -> None:
    _stack_id_ctx.set(stack_id or _DEFAULT_STACK_ID)


def get_stack_id() -> str:
    return _stack_id_ctx.get() or _DEFAULT_STACK_ID
