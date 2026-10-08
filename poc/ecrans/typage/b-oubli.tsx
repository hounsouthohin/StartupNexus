'use client';
// Expérience de typage — variante B : même OUBLI (pas d'« include »). Question : le compilateur
// le voit-il ?
import { useClientQueries } from '@zenstackhq/tanstack-query/react';
import { schema } from '@/zenstack/schema';

export function TitresBOubli() {
    const { data } = useClientQueries(schema).borrowing.useFindMany({});
    return <ul>{data?.map((b) => <li key={b.id}>{b.book.title}</li>)}</ul>;
}
