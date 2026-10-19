import Link from 'next/link';
import { MENU, ROLES_CONNECTES, TITRE } from '@/lib/droits';
import { LIBELLE_ROLE } from '@/lib/roles';

// Accueil. La connexion est SIMULÉE (cookie) jusqu'au branchement de Clerk (N1.5).
// Se connecter CHANGE l'état : c'est un formulaire (POST), jamais un lien — Next précharge les liens
// visibles, et précharger un lien de connexion reviendrait à se connecter (trouvé par les tests d'écran).
// Deux personnes par rôle : pour qu'un essai à la main puisse vérifier que chacun ne voit que ses fiches.
export default function Accueil() {
    return (
        <section className="space-y-4">
            <h1 className="text-2xl font-semibold">{TITRE}</h1>
            <div className="space-y-2 text-sm text-slate-600">
                <p>Se connecter (simulé) :</p>
                {ROLES_CONNECTES.map((r) => (
                    <div key={r} className="flex flex-wrap items-center gap-3">
                        <span className="w-56 font-medium first-letter:uppercase">{LIBELLE_ROLE[r] ?? r}</span>
                        {[1, 2].map((n) => (
                            <form key={n} method="post" action={`/connexion/${r}_${n}:${r}?vers=/`}>
                                <button className="underline">personne {n}</button>
                            </form>
                        ))}
                    </div>
                ))}
                <form method="post" action="/connexion/sortir?vers=/">
                    <button className="underline">visiteur (non connecté)</button>
                </form>
            </div>
            <p className="text-sm">Commencer par : <Link className="underline" href={MENU[0]?.chemin ?? '/'}>{MENU[0]?.libelle}</Link></p>
        </section>
    );
}
