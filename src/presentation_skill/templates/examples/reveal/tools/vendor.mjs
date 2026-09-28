// Copy Reveal and the web fonts from node_modules into vendor/ so the deck runs offline.
// usage: npm install && npm run vendor
import { cpSync, mkdirSync } from "node:fs";
const cp = (a, b) => { cpSync(a, b, { recursive: true }); console.log("vendored", b); };
mkdirSync("vendor/reveal", { recursive: true });
mkdirSync("vendor/fonts", { recursive: true });
for (const f of ["reveal.js", "reveal.css", "reset.css"]) cp(`node_modules/reveal.js/dist/${f}`, `vendor/reveal/${f}`);
cp("node_modules/reveal.js/plugin/notes", "vendor/reveal/notes");
cp("node_modules/@fontsource-variable/fraunces/files/fraunces-latin-full-normal.woff2", "vendor/fonts/fraunces-latin-full-normal.woff2");
cp("node_modules/@fontsource-variable/fraunces/files/fraunces-latin-full-italic.woff2", "vendor/fonts/fraunces-latin-full-italic.woff2");
cp("node_modules/@fontsource-variable/inter/files/inter-latin-opsz-normal.woff2", "vendor/fonts/inter-latin-opsz-normal.woff2");
cp("node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-400-normal.woff2", "vendor/fonts/jetbrains-mono-latin-400-normal.woff2");
cp("node_modules/@fontsource/jetbrains-mono/files/jetbrains-mono-latin-500-normal.woff2", "vendor/fonts/jetbrains-mono-latin-500-normal.woff2");
