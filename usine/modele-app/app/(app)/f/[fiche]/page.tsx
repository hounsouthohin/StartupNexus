'use client';
// Page GÉNÉRIQUE : la liste de n'importe quelle fiche (son nom vient de l'adresse).
import { useParams } from 'next/navigation';
import { ListeDeFiches } from '@/components/pieces';
import { NOTICE, type NomFiche } from '@/lib/notice';

export default function Page() {
    const { fiche } = useParams<{ fiche: string }>();
    if (!(fiche in NOTICE)) return <p className="text-red-700">Fiche inconnue.</p>;
    return <ListeDeFiches fiche={fiche as NomFiche} lienDetail={`/f/${fiche}`} />;
}
