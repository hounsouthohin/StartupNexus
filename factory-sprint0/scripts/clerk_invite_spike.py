"""
scripts/clerk_invite_spike.py
─────────────────────────────
Essai réel de l'attribution d'un rôle par invitation Clerk (USINE.md, phase 3 — porte de décision).

Question testée : un acteur privilégié peut-il inviter quelqu'un avec un rôle, et ce rôle se
retrouve-t-il sur le compte créé via l'invitation (publicMetadata.role, que getCurrentRole() lit) ?

Étapes (dans le conteneur, avec les clés Clerk de DEV du fichier .env) :
  1. python scripts/clerk_invite_spike.py invite <email> <role>   → Clerk envoie l'e-mail d'invitation
  2. la personne ouvre l'e-mail, clique, crée son compte
  3. python scripts/clerk_invite_spike.py check <email>           → affiche le rôle porté par le compte

Utilise l'API Backend de Clerk (createInvitation unitaire — la variante « en masse » a un bug connu
qui ne recopie pas le rôle, issue clerk/javascript #7956).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.clerk.com/v1"


def _call(method: str, path: str, body: dict | None = None):
    key = os.getenv("CLERK_SECRET_KEY") or os.getenv("CLERK_TEST_SECRET_KEY")
    if not key:
        sys.exit("Clé Clerk absente de l'environnement (.env : CLERK_SECRET_KEY ou CLERK_TEST_SECRET_KEY)")
    req = urllib.request.Request(
        f"{API}{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as e:
        sys.exit(f"Clerk a répondu {e.code} : {e.read().decode(errors='replace')[:400]}")


def invite(email: str, role: str) -> None:
    inv = _call("POST", "/invitations", {
        "email_address": email,
        "public_metadata": {"role": role},
        "notify": True,
        "ignore_existing": False,
    })
    print(f"✓ invitation envoyée à {email} — id {inv.get('id')} — statut {inv.get('status')}")
    print(f"  rôle porté par l'invitation : {inv.get('public_metadata')}")
    print("  → ouvrir l'e-mail, cliquer, créer le compte, puis lancer : check", email)


def check(email: str) -> None:
    users = _call("GET", f"/users?email_address={urllib.request.quote(email)}")
    if not users:
        print(f"✗ aucun compte pour {email} (l'invitation n'a pas encore été acceptée ?)")
        invs = _call("GET", "/invitations?status=pending") or []
        mine = [i for i in (invs if isinstance(invs, list) else invs.get("data", [])) if i.get("email_address") == email]
        if mine:
            print(f"  invitation en attente : {mine[0].get('id')} — rôle {mine[0].get('public_metadata')}")
        return
    u = users[0]
    role = (u.get("public_metadata") or {}).get("role")
    print(f"compte {u.get('id')} — publicMetadata : {u.get('public_metadata')}")
    print("✓ le rôle est bien porté par le compte" if role else "✗ le compte n'a PAS de rôle : contournement nécessaire (webhook user.created)")


if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "invite":
        invite(sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 3 and sys.argv[1] == "check":
        check(sys.argv[2])
    else:
        print(__doc__)
        sys.exit(1)
