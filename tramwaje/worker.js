// Pośrednik dla aplikacji "Który tramwaj" (Cloudflare Worker).
// Przepuszcza tylko serwery otwartych danych ZTM Gdańsk i dodaje nagłówek CORS.
export default {
  async fetch(req) {
    const target = new URL(req.url).searchParams.get('url');
    if (!target) return new Response('brak url', { status: 400 });
    const t = new URL(target);
    const ok = ['ckan2.multimediagdansk.pl', 'ckan.multimediagdansk.pl', 'files.cloudgdansk.pl'];
    if (!ok.includes(t.hostname)) return new Response('niedozwolony adres', { status: 403 });
    const r = await fetch(t, { cf: { cacheTtl: 0 } });
    const h = new Headers(r.headers);
    h.delete('content-encoding');
    h.delete('content-length');
    h.set('Access-Control-Allow-Origin', '*');
    h.set('Cache-Control', 'no-store');
    return new Response(r.body, { status: r.status, headers: h });
  }
};
