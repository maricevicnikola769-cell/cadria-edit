# CADRIA EDIT – Windows program

GitHub od ovog foldera pravi:
- **CadriaEdit-Setup.exe**: instalacija (ikonica na radnoj površini i u Start meniju);
- **CadriaEdit-prenosna.zip**: verzija bez instalacije (raspakuj i pokreni `CadriaEdit.exe`).

## Postavljanje na GitHub
1. Na **github.com/new** napravite repozitorijum `cadria-edit`, **Public**.
2. Kliknite **uploading an existing file**, iz ovog foldera označite sve (**Ctrl+A**), prevucite i **Commit changes**.
3. Folder `.github` GitHub preskače, pa: **Add file → Create new file**, ime
   `.github/workflows/build-exe.yml`, nalepite sadržaj istoimenog fajla (otvorite ga Notepad-om) → **Commit changes**.
4. U **Actions** sačekajte zelenu kvačicu (~5 min), pa preuzmite fajlove iz **Releases**.

## Nova verzija editora
Zamenite `html/index.html` novom verzijom (na GitHub-u: otvorite folder `html` → **Add file → Upload files**).
Build se pokreće sam i pravi novu verziju u Releases.

**Važno – u novoj verziji HTML-a moraju ostati dve izmene:**
1. Odmah posle `<meta charset="UTF-8">` red:
   `<script src="desktop-bridge.js"></script>`
   (bez njega export ponovo ide kao preuzimanje kroz browser).
2. Lokalne adrese za izvoz: `import('./lib/mp4-muxer.mjs')` i `import('./lib/webm-muxer.mjs')`
   (umesto `https://cdn.jsdelivr.net/...`). Inače izvoz traži internet.

Ako vam je lakše, pošaljite novu verziju Claude-u da je pripremi.

## Snimanje fajlova
Export videa, titlovi (.srt), projekat (.json), poglavlja i slike snimaju se **direktno na disk**:
otvara se Windows prozor „Sačuvaj kao“, a video se upisuje u fajl dok se pravi.
Na kraju se pojavi poruka „Sačuvano“ sa dugmetom **Prikaži u folderu**.
Kod reda za export (Export Queue) prozor se otvara za svaki fajl posebno.

## Šta radi bez interneta
- Montaža, efekti, titlovi, ugrađeni fontovi, izvoz u MP4/WebM, mikrofon, snimanje fajlova.

## Šta traži internet
- Automatski titlovi (AI model se preuzima prvi put), praćenje lica,
  rezervni MP4 izvoz preko ffmpeg-a (samo kad grafička kartica ne podržava MP4),
  Google fontovi (bez interneta se koriste zamenski).

## Napomene
- Pri prvom pokretanju Windows može prikazati *„Windows protected your PC“* → **More info → Run anyway**.
- Program koristi **Microsoft Edge WebView2**, koji već postoji na Windows 10/11.
  Ako nedostaje, program to javi; besplatno se preuzima sa Microsoft sajta.
- Podešavanja se čuvaju u `%LOCALAPPDATA%\CadriaEdit`.
