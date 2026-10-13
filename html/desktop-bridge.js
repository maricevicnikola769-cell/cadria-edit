/* CADRIA EDIT – dodatak za Windows program (Edge/Chrome prozor aplikacije).
   1) Javlja programu da je prozor otvoren (kad se svi prozori zatvore, program se gasi).
   2) Fajlovi koji bi išli u "Preuzimanja" (titlovi .srt, projekat .json, slike...)
      snimaju se direktno, preko Windows prozora "Sačuvaj kao".
   Export videa već sam koristi "Sačuvaj kao" i upisuje video direktno u fajl.
   U običnom pregledaču (otvoren HTML sa diska) ovaj fajl ne menja ništa. */
(function () {
  'use strict';
  const inApp = location.hostname === '127.0.0.1' && location.port === '47615';
  if (!inApp) return;

  // ---------- 1) znak života ----------
  const ping = () => fetch('/__ping', { cache: 'no-store' }).catch(() => {});
  ping();
  setInterval(ping, 10000);

  // ---------- 2) <a download> -> "Sačuvaj kao" ----------
  if (!window.showSaveFilePicker) return;
  const pendingUrls = new Set();
  const origRevoke = URL.revokeObjectURL.bind(URL);
  URL.revokeObjectURL = function (u) {
    if (pendingUrls.has(u)) return; // oslobađa se tek kad se fajl sačuva
    return origRevoke(u);
  };
  const origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    const href = this.href || '';
    const active = !navigator.userActivation || navigator.userActivation.isActive;
    if (!this.hasAttribute('download') || !/^(blob|data):/i.test(href) || !active) {
      return origClick.call(this); // npr. red za export: obično preuzimanje
    }
    const a = this;
    const name = a.getAttribute('download') || 'fajl';
    const ext = (name.match(/\.([a-z0-9]+)$/i) || [])[1];
    const opts = { suggestedName: name };
    if (ext) opts.types = [{ description: ext.toUpperCase() + ' fajl', accept: { 'application/octet-stream': ['.' + ext] } }];
    if (href.startsWith('blob:')) pendingUrls.add(href);
    const blobP = fetch(href).then(r => r.blob());
    const done = () => { if (pendingUrls.delete(href)) setTimeout(() => origRevoke(href), 1000); };
    window.showSaveFilePicker(opts).then(async handle => {
      const w = await handle.createWritable();
      await w.write(await blobP);
      await w.close();
      done();
    }).catch(err => {
      if (err && err.name === 'AbortError') { done(); return; } // korisnik je otkazao
      // dijalog nije mogao da se otvori -> obično preuzimanje
      origClick.call(a);
      setTimeout(done, 5000);
    });
  };
})();
