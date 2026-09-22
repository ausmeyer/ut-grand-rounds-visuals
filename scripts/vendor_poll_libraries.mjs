// Reproduce the local browser libraries after npm ci. No CDN is needed at runtime.
import { copyFile, mkdir } from 'node:fs/promises';
const root = new URL('../', import.meta.url);
const vendor = new URL('docs/assets/poll-01/vendor/', root);
await mkdir(vendor, { recursive:true });
for (const [source, destination] of [
  ['node_modules/@supabase/supabase-js/dist/umd/supabase.js','supabase.js'],
  ['node_modules/@supabase/supabase-js/LICENSE','supabase.LICENSE'],
  ['node_modules/qrcode-generator/dist/qrcode.js','qrcode.js'],
]) await copyFile(new URL(source,root),new URL(destination,vendor));
console.log('Vendored pinned Supabase and QR libraries; QR license retained in its source header.');
