"""transitionTo — machine à états (type I).

Fait avancer une entité d'un état à un autre ET capte les champs liés à CETTE
transition (« refusée AVEC UN MOTIF » → rejectionReason au moment du refus).

Pourquoi ce module existe (bug constaté notes-frais 17 Juil) : la garde de update()
verrouille les champs métier dès qu'on quitte l'état initial. Or refuser = partir de
`submitted` (verrouillé) EN écrivant rejectionReason → update() lève « fiche non
modifiable ». Le motif était donc INATTEIGNABLE. transitionTo est le chemin béni :
il n'écrit QUE le statut cible + les state_fields déclarés pour cet état, donc il
contourne le verrou sans jamais l'ouvrir aux autres champs.
"""
from __future__ import annotations

from .base import ServiceMethodModule, MethodDecl


class TransitionModule(ServiceMethodModule):
    def should_activate(self, ctx) -> bool:
        return getattr(ctx, "status_flow", None) is not None

    def methods_for(self, ctx) -> list[MethodDecl]:
        return [MethodDecl(
            "transitionTo",
            f"({ctx.owner}: string, id: string, newStatus: string, data?) → Promise<{ctx.serialized_type}>"
            "  (change l'état + capte les champs de la transition)",
        )]

    def generate(self, ctx, **kwargs) -> list[str]:
        flow = ctx.status_flow
        owner = ctx.owner
        camel = ctx.camel
        name = ctx.name
        serialized = ctx.serialized_type
        field = flow.field

        _allowed = "{ " + ", ".join(
            f"{_s}: [{', '.join(repr(_t) for _t in _nxt)}]"
            for _s, _nxt in sorted(flow.transitions.items())
        ) + " }"
        _fields_by_state = (
            "{ " + ", ".join(
                f"{_s}: [{', '.join(repr(_f) for _f in _fs)}]"
                for _s, _fs in sorted(flow.state_fields.items())
            ) + " }"
        ) if flow.state_fields else "{}"

        return [
            "",
            f"  transitionTo: async ({owner}: string, id: string, newStatus: string, data: Partial<Update{name}Input> = {{}}): Promise<{serialized}> => {{",
            f"    const _cur = await prisma.{camel}.findFirst({{ where: {{ id, {owner} }}, select: {{ {field}: true }} }})",
            "    if (!_cur) notFound()",
            f"    const _allowed: Record<string, string[]> = {_allowed}",
            f"    if (!(_allowed[_cur.{field}] ?? []).includes(newStatus)) {{",
            f"      throw new Error(`Transition interdite : ${{_cur.{field}}} → ${{newStatus}}`)",
            "    }",
            "    // Seuls les champs déclarés pour l'état CIBLE sont écrits — jamais un champ",
            "    // métier arbitraire (sinon transitionTo rouvrirait le verrou d'édition).",
            f"    const _fieldsByState: Record<string, string[]> = {_fields_by_state}",
            "    const _keep = new Set(_fieldsByState[newStatus] ?? [])",
            f"    const _payload: Partial<Update{name}Input> = {{}}",
            "    for (const _k of Object.keys(data)) {",
            "      if (_keep.has(_k) && (data as Record<string, unknown>)[_k] !== undefined) {",
            "        (_payload as Record<string, unknown>)[_k] = (data as Record<string, unknown>)[_k]",
            "      }",
            "    }",
            f"    const result = await prisma.{camel}.update({{ where: {{ id, {owner} }}, data: {{ ..._payload, {field}: newStatus as {name}['{field}'] }} }})",
            "    return _serialize(result)",
            "  },",
        ]
