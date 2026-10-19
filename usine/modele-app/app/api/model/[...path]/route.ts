// L'API générée par ZenStack (/api/model/<modèle>/<opération>) : chaque requête passe par le
// client AVEC règles, au nom de l'utilisateur connecté.
import { RPCApiHandler } from '@zenstackhq/server/api';
import { NextRequestHandler } from '@zenstackhq/server/next';
import { dbFor } from '@/lib/db';
import { getUser } from '@/lib/session';
import { schema } from '@/zenstack/schema';

// (N1.3) les refus et erreurs du serveur vont dans son journal : sans cela, l'écran ne disait que « An error
// occurred while fetching the data » et la cause restait invisible (échec intermittent du 10 oct)
const handler = NextRequestHandler({
    apiHandler: new RPCApiHandler({ schema, log: ['warn', 'error'] }),
    getClient: async () => dbFor(await getUser()),
    useAppDir: true,
});

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
