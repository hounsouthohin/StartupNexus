// Démo seulement : /connexion/adherent_1:adherent pose le cookie de session simulée ;
// /connexion/sortir le retire.
import { NextResponse, type NextRequest } from 'next/server';

export async function GET(req: NextRequest, { params }: { params: Promise<{ qui: string }> }) {
    const { qui } = await params;
    const res = NextResponse.redirect(new URL(req.nextUrl.searchParams.get('vers') ?? '/', req.url));
    if (qui === 'sortir') res.cookies.delete('poc_user');
    else res.cookies.set('poc_user', decodeURIComponent(qui), { path: '/' });
    return res;
}
