// L'API générée par ZenStack (/api/model/<modèle>/<opération>) : chaque requête passe par le
// client AVEC règles, au nom de l'utilisateur connecté.
import { RPCApiHandler } from '@zenstackhq/server/api';
import { NextRequestHandler } from '@zenstackhq/server/next';
import { dbFor } from '@/lib/db';
import { getUser } from '@/lib/session';
import { schema } from '@/zenstack/schema';

const handler = NextRequestHandler({
    apiHandler: new RPCApiHandler({ schema }),
    getClient: async () => dbFor(await getUser()),
    useAppDir: true,
});

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
