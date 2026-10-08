'use client';
// Page GÉNÉRIQUE : le détail de n'importe quelle fiche, avec son bloc de décision.
import { useParams } from 'next/navigation';
import { FicheDetail } from '@/components/pieces';
import { NOTICE, type NomFiche } from '@/lib/notice';

export default function Page() {
    const { fiche, id } = useParams<{ fiche: string; id: string }>();
    if (!(fiche in NOTICE)) return <p className="text-red-700">Fiche inconnue.</p>;
    return <FicheDetail fiche={fiche as NomFiche} id={id} />;
}
