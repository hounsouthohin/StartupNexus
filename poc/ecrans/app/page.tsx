import Link from 'next/link';

export default function Accueil() {
    const roles = [['adherent_1:adherent', 'adhérent'], ['bibliothecaire_1:bibliothecaire', 'bibliothécaire']];
    return (
        <main className="mx-auto max-w-xl space-y-4 p-8">
            <h1 className="text-2xl font-semibold">E6 — deux plomberies, mêmes écrans</h1>
            <p><Link className="underline" href="/a/catalogue">Variante A (Refine)</Link> · <Link className="underline" href="/b/catalogue">Variante B (nos pièces)</Link></p>
            <p className="text-sm">Se connecter (simulé) :{' '}
                {roles.map(([qui, nom]) => (
                    <Link key={qui} className="mr-3 underline" href={`/connexion/${qui}?vers=/b/catalogue`}>{nom}</Link>
                ))}
                <Link className="underline" href="/connexion/sortir?vers=/">visiteur</Link>
            </p>
        </main>
    );
}
