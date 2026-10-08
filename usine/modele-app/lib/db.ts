import { ZenStackClient } from '@zenstackhq/orm';
import { PostgresDialect } from '@zenstackhq/orm/dialects/postgres';
import { PolicyPlugin } from '@zenstackhq/plugin-policy';
import { Pool } from 'pg';
import { schema } from '../zenstack/schema';

// Client SANS règles : réservé au serveur (données de départ, profil créé à la première visite).
export const rawDb = new ZenStackClient(schema, {
    dialect: new PostgresDialect({ pool: new Pool({ connectionString: process.env.DATABASE_URL }) }),
});
const policyDb = rawDb.$use(new PolicyPlugin());

export type User = { id: string; role: string };
// Client AVEC règles : tout ce qui vient d'un utilisateur passe par lui.
export const dbFor = (user: User | null) => (user ? policyDb.$setAuth(user) : policyDb);
