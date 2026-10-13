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
   (bez njega se program ne gasi sam i titlovi/projekat idu u Preuzimanja).
2. Lokalne adrese za izvoz: `import('./lib/mp4-muxer.mjs')` i `import('./lib/webm-muxer.mjs')`
   (umesto `https://cdn.jsdelivr.net/...`). Inače izvoz traži internet.

Ako vam je lakše, pošaljite novu verziju Claude-u da je pripremi.

## Kako program radi
Program otvara editor u **Microsoft Edge-u** (ili Chrome-u) kao poseban prozor, bez adresne trake.
Zato sve radi isto kao u pregledaču: AI popravka, praćenje lica, export, mikrofon.
Kad zatvorite prozor, program se sam ugasi (posle ~1 minuta).

## Snimanje fajlova
Export videa, titlovi (.srt), projekat (.json), poglavlja i slike snimaju se **direktno na disk**
preko prozora „Sačuvaj kao“; video se upisuje u fajl dok se pravi.
Kod reda za export (Export Queue) fajlovi idu u folder Preuzimanja.

## Šta radi bez interneta
- Montaža, efekti, titlovi, ugrađeni fontovi, izvoz u MP4/WebM, mikrofon, snimanje fajlova.

## Šta traži internet
- AI popravka rezolucije i automatski titlovi (AI model se preuzima prvi put), praćenje lica,
  rezervni MP4 izvoz preko ffmpeg-a, Google fontovi (bez interneta se koriste zamenski).

## Napomene
- Pri prvom pokretanju Windows može prikazati *„Windows protected your PC“* → **More info → Run anyway**.
- Potreban je Microsoft Edge (postoji na svakom Windows 10/11) ili Google Chrome.
- Podešavanja se čuvaju u `%LOCALAPPDATA%\CadriaEdit`.
