/* CADRIA EDIT – most između editora i Windows programa.
   U programu (pywebview) svako snimanje ide DIREKTNO na disk preko Windows dijaloga
   "Sačuvaj kao", bez preuzimanja kroz browser:
   - window.showSaveFilePicker  -> Windows dijalog + upis u fajl (i tokom exporta, deo po deo)
   - <a download href="blob:..."> -> Windows dijalog + upis u fajl
   U običnom browseru (bez pywebview) ovaj fajl ne menja ništa. */
(function () {
  'use strict';
  const native = () => !!(window.pywebview && window.pywebview.api && window.pywebview.api.ask_save);
  const api = () => window.pywebview.api;

  let token = null;
  async function getToken() {
    if (!token) token = await api().get_token();
    return token;
  }
  async function post(path, params, body) {
    const q = new URLSearchParams(params).toString();
    const r = await fetch('/__file/' + path + '?' + q, {
      method: 'POST',
      headers: { 'X-Cadria-Token': await getToken() },
      body: body === undefined ? null : body,
    });
    if (!r.ok) throw new Error('Upis na disk nije uspeo (' + r.status + '): ' + (await r.text()));
  }
  function toBody(d) {
    if (d == null) return new Uint8Array(0);
    if (typeof d === 'string') return new TextEncoder().encode(d);
    if (d instanceof Blob || d instanceof ArrayBuffer) return d;
    if (ArrayBuffer.isView(d)) return new Uint8Array(d.buffer, d.byteOffset, d.byteLength);
    return new TextEncoder().encode(String(d));
  }
  function sizeOf(b) { return b instanceof Blob ? b.size : b.byteLength; }

  function abortError() {
    try { return new DOMException('Korisnik je otkazao snimanje.', 'AbortError'); }
    catch (e) { const er = new Error('Korisnik je otkazao snimanje.'); er.name = 'AbortError'; return er; }
  }

  async function askSave(suggestedName, exts) {
    const res = await api().ask_save(suggestedName || 'fajl', exts || []);
    if (!res) throw abortError();
    return res; // { id, name, path }
  }

  // ---------- Toast "Sačuvano" ----------
  function toast(info) {
    let el = document.getElementById('__cadria_toast');
    if (!el) {
      el = document.createElement('div');
      el.id = '__cadria_toast';
      el.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:2147483647;max-width:min(520px,calc(100vw - 32px));' +
        'background:#1d2a1f;color:#e8f6ea;border:1px solid #3d7a4a;border-radius:10px;padding:12px 14px;' +
        'font:14px/1.4 system-ui,Segoe UI,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.35);display:flex;gap:12px;align-items:center';
      document.body.appendChild(el);
    }
    el.innerHTML = '';
    const t = document.createElement('div');
    t.style.cssText = 'min-width:0;overflow-wrap:anywhere';
    t.textContent = '✅ Sačuvano: ' + info.path;
    const b = document.createElement('button');
    b.textContent = 'Prikaži u folderu';
    b.style.cssText = 'flex:none;font:inherit;font-weight:600;background:#3d7a4a;color:#fff;border:0;border-radius:8px;padding:6px 10px;cursor:pointer';
    b.onclick = () => { try { api().reveal(info.id); } catch (e) {} };
    const x = document.createElement('button');
    x.textContent = '✕';
    x.style.cssText = 'flex:none;font:inherit;background:transparent;color:inherit;border:0;cursor:pointer';
    x.onclick = () => el.remove();
    el.append(t, b, x);
    clearTimeout(el.__t);
    el.__t = setTimeout(() => el.remove(), 12000);
  }

  // ---------- Writable koji piše pravo u fajl ----------
  function makeWritable(info) {
    let cursor = 0;
    let closed = false;
    const opened = post('open', { id: info.id });
    async function write(arg) {
      await opened;
      if (arg && typeof arg === 'object' && !(arg instanceof Blob) && !(arg instanceof ArrayBuffer) &&
          !ArrayBuffer.isView(arg) && 'type' in arg) {
        if (arg.type === 'seek') { cursor = arg.position; return; }
        if (arg.type === 'truncate') { await post('truncate', { id: info.id, size: arg.size }); if (cursor > arg.size) cursor = arg.size; return; }
        if (arg.type === 'write') {
          const pos = arg.position != null ? arg.position : cursor;
          const body = toBody(arg.data);
          await post('write', { id: info.id, pos }, body);
          cursor = pos + sizeOf(body);
          return;
        }
      }
      const body = toBody(arg);
      await post('write', { id: info.id, pos: cursor }, body);
      cursor += sizeOf(body);
    }
    return {
      write,
      seek: async (p) => { cursor = p; },
      truncate: async (s) => write({ type: 'truncate', size: s }),
      close: async () => {
        if (closed) return; closed = true;
        await opened;
        await post('close', { id: info.id });
        toast(info);
      },
      abort: async () => { closed = true; try { await post('close', { id: info.id }); } catch (e) {} },
    };
  }

  // ---------- showSaveFilePicker ----------
  const origPicker = window.showSaveFilePicker ? window.showSaveFilePicker.bind(window) : null;
  window.showSaveFilePicker = async function (opts) {
    if (!native()) {
      if (origPicker) return origPicker(opts);
      throw new TypeError('showSaveFilePicker nije dostupan');
    }
    opts = opts || {};
    const exts = [];
    (opts.types || []).forEach(t => Object.values(t.accept || {}).forEach(a => [].concat(a).forEach(e => exts.push(String(e).replace(/^\./, '')))));
    const info = await askSave(opts.suggestedName, exts);
    return {
      kind: 'file',
      name: info.name,
      createWritable: async () => makeWritable(info),
      getFile: async () => { throw new Error('Čitanje nije podržano'); },
      queryPermission: async () => 'granted',
      requestPermission: async () => 'granted',
    };
  };

  // ---------- <a download> sa blob:/data: adresom ----------
  const pendingUrls = new Set();
  const origRevoke = URL.revokeObjectURL.bind(URL);
  URL.revokeObjectURL = function (u) {
    if (pendingUrls.has(u)) return; // oslobađa se tek kad se fajl sačuva
    return origRevoke(u);
  };
  const origClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function () {
    const href = this.href || '';
    if (native() && this.hasAttribute('download') && /^(blob|data):/i.test(href)) {
      const name = this.getAttribute('download') || 'fajl';
      const ext = (name.match(/\.([a-z0-9]+)$/i) || [])[1];
      if (href.startsWith('blob:')) pendingUrls.add(href);
      const blobP = fetch(href).then(r => r.blob());
      (async () => {
        try {
          const blob = await blobP;
          const info = await askSave(name, ext ? [ext] : []);
          const w = makeWritable(info);
          await w.write(blob);
          await w.close();
        } catch (e) {
          if (!e || e.name !== 'AbortError') alert('Snimanje fajla nije uspelo: ' + (e && e.message ? e.message : e));
        } finally {
          if (pendingUrls.delete(href)) setTimeout(() => origRevoke(href), 1000);
        }
      })();
      return;
    }
    return origClick.call(this);
  };
})();
