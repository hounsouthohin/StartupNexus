from temporalio import activity
from temporalio.exceptions import ApplicationError
import asyncio
import os
import sys
from typing import Dict, Any

# Validation contrats
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from scripts.validate_contracts import validate_input, validate_output

# Github est importé ici pour éviter les problèmes au démarrage du worker
from github import Github, GithubException


@activity.defn(name="github_activity")
async def github_activity(input_data: Dict[str, Any], run_id: str = "") -> Dict[str, str]:
    """
    Crée un repo GitHub, pousse les fichiers générés sur la branche 'dev',
    et ouvre une Pull Request vers main si nécessaire.
    """
    try:
        from agents.shared_tools import set_run_id, set_stack_id
        set_run_id(run_id)
        set_stack_id(str(input_data.get("stack_id", "nextjs-clerk-prisma")))
    except Exception:
        pass
    input_data["run_id"] = run_id
    # 1. Validation entrée stricte
    validate_input("github_agent", input_data)

    files = input_data.get("files", {})
    project_name = input_data.get("project_name", "projet-sans-nom")
    build_success = bool(input_data.get("build_success", True))
    spec_coverage = float(input_data.get("spec_coverage", 1.0))
    spec_validation_status = str(input_data.get("spec_validation_status", "OK"))
    _SPEC_COVERAGE_THRESHOLD = 0.5  # même seuil que SPEC_COVERAGE_SUCCESS_THRESHOLD workflow

    if not files:
        raise ApplicationError("INVALID_INPUT", "Aucun fichier fourni pour le push GitHub")

    activity.logger.info(f"GitHub activity démarrée → Projet: {project_name} | {len(files)} fichiers")

    # 2. Vérification token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ApplicationError("MISSING_CONFIGURATION", "GITHUB_TOKEN manquant")

    # 3. Connexion GitHub
    try:
        g = Github(github_token)
        user = g.get_user()
    except Exception as e:
        raise ApplicationError("GITHUB_AUTH_FAILED", f"Échec authentification GitHub: {str(e)}")

    repo_name = f"saas-{project_name.lower().replace(' ', '-')}"
    repo_url = f"https://github.com/{user.login}/{repo_name}"

    # 4. Création ou récupération du repo
    try:
        repo = user.get_repo(repo_name)
        activity.logger.info(f"Repo existant : {repo_url}")
    except GithubException as e:
        if e.status == 404:
            try:
                repo = user.create_repo(
                    repo_name,
                    private=True,
                    description=f"SaaS généré par Factory Nexus pour {project_name}"
                )
                activity.logger.info(f"Repo créé : {repo_url}")
            except Exception as create_err:
                raise ApplicationError("REPO_CREATION_FAILED", str(create_err))
        else:
            raise ApplicationError("GITHUB_API_ERROR", str(e))

    # 5. Gestion branche principale + initialisation si vide
    main_branch = repo.default_branch or "main"

    try:
        repo.get_branch(main_branch)
        is_empty = False
    except GithubException:
        is_empty = True

    if is_empty and files:
        # Ajout README par défaut si absent
        if "README.md" not in files:
            files["README.md"] = f"# {project_name}\n\nGénéré par Factory Nexus AI Agent Factory."

        # Premier commit sur main pour initialiser le repo
        path, content = next(iter(files.items()))
        files.pop(path)  # on enlève pour ne pas le repusher sur dev

        try:
            repo.create_file(
                path,
                f"Initial commit: {path}",
                content,
                branch=main_branch
            )
            activity.logger.info(f"Repo initialisé avec {path} sur {main_branch}")
        except Exception as e:
            raise ApplicationError("INITIAL_COMMIT_FAILED", str(e))

    # 6. Création / vérification branche dev
    dev_branch = "dev"
    try:
        repo.get_branch(dev_branch)
    except GithubException:
        main_sha = repo.get_branch(main_branch).commit.sha
        repo.create_git_ref(f"refs/heads/{dev_branch}", main_sha)
        activity.logger.info(f"Branche '{dev_branch}' créée depuis {main_branch}")

    # 7. Push des fichiers sur dev (avec retry exponentiel sur 429)
    for path, content in files.items():
        for attempt in range(3):
            try:
                try:
                    contents = repo.get_contents(path, ref=dev_branch)
                    repo.update_file(
                        path,
                        f"Update {path} (généré par Agent Factory)",
                        content,
                        contents.sha,
                        branch=dev_branch
                    )
                    activity.logger.info(f"→ Mise à jour {path}")
                except GithubException as e:
                    if e.status == 404:
                        repo.create_file(
                            path,
                            f"Create {path} (généré par Agent Factory)",
                            content,
                            branch=dev_branch
                        )
                        activity.logger.info(f"→ Création {path}")
                    elif e.status == 429:
                        raise  # propagé au retry ci-dessous
                    else:
                        raise ApplicationError("FILE_PUSH_FAILED", f"Échec sur {path}: {str(e)}")
                break  # succès — sortir du retry
            except GithubException as e:
                if e.status == 429 and attempt < 2:
                    wait = 10 * (2 ** attempt)  # 10s, 20s
                    activity.logger.warning(f"GitHub rate-limit (429) sur {path} – retry dans {wait}s")
                    await asyncio.sleep(wait)
                else:
                    raise ApplicationError("FILE_PUSH_FAILED", f"429 non résolu sur {path}: {str(e)}")

    # 8. Création ou récupération PR
    try:
        pulls = repo.get_pulls(state="open", head=dev_branch, base=main_branch)
        if pulls.totalCount > 0:
            pr = pulls[0]
            activity.logger.info(f"PR existante trouvée : {pr.html_url}")
            output = {"pr_url": pr.html_url, "repo_url": repo_url}
        else:
            pr = repo.create_pull(
                title=f"feat: Génération initiale pour {project_name}",
                body="Code full-stack généré automatiquement par Factory Nexus AI.",
                base=main_branch,
                head=dev_branch
            )
            activity.logger.info(f"PR créée : {pr.html_url}")
            output = {"pr_url": pr.html_url, "repo_url": repo_url}

        # 8b. Label needs-spec-alignment si build échoué ou spec insuffisante
        _needs_label = (
            not build_success
            or spec_coverage < _SPEC_COVERAGE_THRESHOLD
            or spec_validation_status == "DEGRADED"
        )
        if _needs_label:
            try:
                _label_name = "needs-spec-alignment"
                # Créer le label s'il n'existe pas
                try:
                    repo.get_label(_label_name)
                except GithubException:
                    repo.create_label(_label_name, "e11d48", "Build échoué ou spec DEGRADED — non mergeable")
                pr.add_to_labels(_label_name)
                activity.logger.warning(
                    f"Label '{_label_name}' appliqué — "
                    f"build_success={build_success}, "
                    f"spec_coverage={spec_coverage:.0%}, "
                    f"spec_status={spec_validation_status}"
                )
            except Exception as _label_err:
                activity.logger.warning(f"Label non appliqué (non bloquant): {_label_err}")

        # 9. Validation sortie
        validate_output("github_agent", output)

        return output

    except Exception as e:
        activity.logger.error(f"Échec final GitHub activity: {str(e)}", exc_info=True)
        raise ApplicationError("GITHUB_ACTIVITY_FAILED", str(e))
