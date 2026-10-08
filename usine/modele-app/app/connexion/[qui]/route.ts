// Connexion SIMULÉE (jusqu'au branchement de Clerk en N1.5) : POST /connexion/<id>:<rôle> pose le
// cookie de session ; POST /connexion/sortir le retire. Jamais en GET : un GET peut être préchargé.
import { NextResponse, type NextRequest } from 'next/server';

export async function POST(req: NextRequest, { params }: { params: Promise<{ qui: string }> }) {
    const { qui } = await params;
    // 303 : après un envoi de formulaire, le navigateur revient sur la page en simple lecture
    const res = NextResponse.redirect(new URL(req.nextUrl.searchParams.get('vers') ?? '/', req.url), 303);
    if (qui === 'sortir') res.cookies.delete('session_usine');
    else res.cookies.set('session_usine', decodeURIComponent(qui), { path: '/' });
    return res;
}
