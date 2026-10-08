'use client';
// Expérience de typage — variante A : on a OUBLIÉ de demander l'ouvrage lié (pas d'« include »),
// mais le type déclaré à la main affirme qu'il est là. Question : le compilateur le voit-il ?
import { useList } from '@refinedev/core';
import type { Book, Borrowing } from '@/zenstack/models';

export function TitresAOubli() {
    const { result } = useList<Borrowing & { book: Book }>({ resource: 'Borrowing' });
    return <ul>{result.data.map((b) => <li key={b.id}>{b.book.title}</li>)}</ul>;
}
