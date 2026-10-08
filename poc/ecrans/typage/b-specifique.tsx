'use client';
// Expérience de typage — variante B (fonctions générées par ZenStack) : code SPÉCIFIQUE, correct.
// Le type n'est pas déclaré : il est DÉDUIT de la requête (le « include » ajoute « book »).
import { useClientQueries } from '@zenstackhq/tanstack-query/react';
import { schema } from '@/zenstack/schema';

export function TitresB() {
    const { data } = useClientQueries(schema).borrowing.useFindMany({ include: { book: true } });
    return <ul>{data?.map((b) => <li key={b.id}>{b.book.title}</li>)}</ul>;
}
