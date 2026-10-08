'use client';
// Expérience de typage — variante A (Refine) : code SPÉCIFIQUE, correct. Le type est DÉCLARÉ à la
// main (Refine ne sait rien du schéma) ; on utilise les types générés par ZenStack.
import { useList } from '@refinedev/core';
import type { Book, Borrowing } from '@/zenstack/models';

export function TitresA() {
    const { result } = useList<Borrowing & { book: Book }>({ resource: 'Borrowing', meta: { include: { book: true } } });
    return <ul>{result.data.map((b) => <li key={b.id}>{b.book.title}</li>)}</ul>;
}
