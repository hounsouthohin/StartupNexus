"""L'appel à l'IA, commun à tous les lecteurs : réponse en JSON, contrôlée par programme, refusée
avec l'erreur précise et redemandée (2 essais de plus — règle 3), jetons et dollars comptés.

PLAFOND : chaque lancement a un plafond de dépense (0,20 $ par défaut, règle de budget). Il est
vérifié avant chaque appel : dépassé, le lancement s'arrête de lui-même.
"""
from __future__ import annotations

import json
import os
import time

from pydantic import ValidationError

# $ US par million de jetons (entrée, sortie), relevés le 7 oct 2026 ; les jetons de réflexion
# des modèles qui raisonnent sont comptés en sortie.
PRIX = {"gpt-5.4-mini": (0.75, 4.50), "gpt-5.5": (5.00, 30.00), "gemini-pro-latest": (2.00, 12.00)}
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class PlafondAtteint(RuntimeError):
    pass


class Budget:
    def __init__(self, modele: str, plafond: float):
        if modele not in PRIX:
            raise SystemExit(f"modèle « {modele} » sans prix connu (usine/comprendre/ia.py) : coût incalculable, refusé")
        self.modele, self.plafond = modele, plafond
        self.entree = self.sortie = self.appels = 0

    @property
    def depense(self) -> float:
        pe, ps = PRIX[self.modele]
        return self.entree / 1e6 * pe + self.sortie / 1e6 * ps

    def verifier(self) -> None:
        if self.depense >= self.plafond:
            raise PlafondAtteint(f"plafond de {self.plafond:.2f} $ atteint ({self.depense:.3f} $ dépensés) : arrêt")

    def bilan(self) -> dict:
        return {"modele": self.modele, "appels": self.appels, "jetons_entree": self.entree,
                "jetons_sortie": self.sortie, "dollars": round(self.depense, 4), "plafond": self.plafond}


def client_pour(modele: str):
    from dotenv import load_dotenv
    from openai import OpenAI
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[2] / "factory-sprint0" / ".env")
    if modele.startswith("gemini"):
        cle = os.getenv("GEMINI_API_KEY")
        if not cle:
            raise SystemExit("GEMINI_API_KEY absente de factory-sprint0/.env")
        return OpenAI(api_key=cle, base_url=GEMINI_URL)
    return OpenAI()


def _appel(client, **kwargs):
    """Patience sur un engorgement passager ; arrêt immédiat sur un compte sans crédit."""
    from openai import APIConnectionError, APITimeoutError, InternalServerError, RateLimitError
    for attente in (15, 30, 60):
        try:
            return client.chat.completions.create(**kwargs)
        except (InternalServerError, APIConnectionError, APITimeoutError) as e:
            print(f"   (fournisseur indisponible : {str(e)[:80]} — nouvel essai dans {attente} s)", flush=True)
            time.sleep(attente)
        except RateLimitError as e:
            if any(k in str(e) for k in ("insufficient_quota", "credit_balance", "PerDay", "limit: 0")):
                raise SystemExit(f"Plus de crédit ou quota épuisé chez ce fournisseur : {e}")
            print(f"   (limite de débit, nouvel essai dans {attente} s)", flush=True)
            time.sleep(attente)
    return client.chat.completions.create(**kwargs)


def demander(client, budget: Budget, consigne: str, donnees: dict, forme, controle, ctx: dict, journal: list):
    """Pose UNE question ; renvoie la réponse acceptée, ou None après 3 refus."""
    messages = [{"role": "system", "content": consigne},
                {"role": "user", "content": json.dumps(donnees, ensure_ascii=False)}]
    extra = {} if budget.modele.startswith(("gpt-5", "o", "gemini")) else {"temperature": 0}
    for essai in range(1, 4):
        budget.verifier()
        rep = _appel(client, model=budget.modele, messages=messages, response_format={"type": "json_object"}, **extra)
        texte = rep.choices[0].message.content or ""
        u = getattr(rep, "usage", None)
        budget.entree += getattr(u, "prompt_tokens", 0) or 0
        budget.sortie += getattr(u, "completion_tokens", 0) or 0
        budget.appels += 1
        try:
            sortie = forme.model_validate_json(texte)
            erreurs = controle(sortie, ctx)
        except ValidationError as e:
            sortie, erreurs = None, [f"{'.'.join(map(str, x['loc']))} : {x['msg']}" for x in e.errors()][:15]
        journal.append({"lecteur": forme.__name__, "essai": essai, "erreurs": erreurs,
                        "jetons_entree": getattr(u, "prompt_tokens", 0) or 0,
                        "jetons_sortie": getattr(u, "completion_tokens", 0) or 0})
        if sortie is not None and not erreurs:
            return sortie
        messages += [{"role": "assistant", "content": texte},
                     {"role": "user", "content": "Réponse refusée :\n- " + "\n- ".join(erreurs)
                      + "\nCorrige et renvoie le JSON complet."}]
    return None
