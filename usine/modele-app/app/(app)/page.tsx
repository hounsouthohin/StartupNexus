import Link from 'next/link';
import { MENU, ROLES_CONNECTES, TITRE } from '@/lib/droits';

// Accueil. La connexion est SIMULÉE (cookie) jusqu'au branchement de Clerk (N1.5).
// Se connecter CHANGE l'état : c'est un formulaire (POST), jamais un lien — Next précharge les liens
// visibles, et précharger un lien de connexion reviendrait à se connecter (trouvé par les tests d'écran).
export default function Accueil() {
    return (
        <section className="space-y-4">
            <h1 className="text-2xl font-semibold">{TITRE}</h1>
            <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                <span>Se connecter (simulé) :</span>
                {ROLES_CONNECTES.map((r) => (
                    <form key={r} method="post" action={`/connexion/${r}_1:${r}?vers=/`}>
                        <button className="underline">{r}</button>
                    </form>
                ))}
                <form method="post" action="/connexion/sortir?vers=/">
                    <button className="underline">visiteur</button>
                </form>
            </div>
            <p className="text-sm">Commencer par : <Link className="underline" href={MENU[0]?.chemin ?? '/'}>{MENU[0]?.libelle}</Link></p>
        </section>
    );
}
