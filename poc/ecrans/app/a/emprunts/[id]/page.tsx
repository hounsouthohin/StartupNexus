'use client';
import { useParams } from 'next/navigation';
import { FicheDetail } from '@/components/a/pieces';

export default function Page() {
    const { id } = useParams<{ id: string }>();
    return <FicheDetail fiche="Borrowing" id={id} />;
}
