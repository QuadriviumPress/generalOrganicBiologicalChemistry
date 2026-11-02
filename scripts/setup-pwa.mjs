import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import sharp from 'sharp';
import YAML from 'yaml';

const root = process.cwd();
const output = path.join(root, '_build', 'html');
const config = YAML.parse(fs.readFileSync(path.join(root, 'myst.yml'), 'utf8'));
const rawBase = process.env.BASE_URL || '/';
const basePath = rawBase === '/' ? '/' : `/${rawBase.replace(/^\/+|\/+$/g, '')}/`;
const url = (name = '') => `${basePath}${name}`.replace(/\/+/g, '/');

if (!fs.existsSync(output)) throw new Error('Missing _build/html; run MyST before PWA setup.');

const title = config.project?.title || config.site?.title || 'MyST Book';
const shortName = config.project?.short_title || title;
const description = config.project?.description || `Read ${title} online or offline.`;
const manifest = {
  name: title,
  short_name: shortName,
  description,
  start_url: basePath,
  scope: basePath,
  display: 'standalone',
  background_color: '#ffffff',
  theme_color: '#315c8c',
  categories: ['books', 'education'],
  icons: [192, 512].flatMap((size) => [
    { src: url(`icons/icon-${size}.png`), sizes: `${size}x${size}`, type: 'image/png', purpose: 'any' },
    { src: url(`icons/icon-${size}-maskable.png`), sizes: `${size}x${size}`, type: 'image/png', purpose: 'maskable' }
  ])
};

fs.mkdirSync(path.join(output, 'icons'), { recursive: true });
fs.writeFileSync(path.join(output, 'manifest.webmanifest'), `${JSON.stringify(manifest, null, 2)}\n`);
for (const file of ['offline.html', 'service-worker.js']) {
  fs.copyFileSync(path.join(root, 'pwa', file), path.join(output, file));
}

for (const size of [192, 512]) {
  await sharp(path.join(root, 'images', 'logo.svg')).resize(size, size).png().toFile(path.join(output, 'icons', `icon-${size}.png`));
  await sharp(path.join(root, 'images', 'logo.svg')).resize(size, size, { fit: 'contain', background: '#315c8c' }).png().toFile(path.join(output, 'icons', `icon-${size}-maskable.png`));
}

const htmlFiles = [];
function collect(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const target = path.join(dir, entry.name);
    if (entry.isDirectory()) collect(target);
    else if (entry.name.endsWith('.html')) htmlFiles.push(target);
  }
}
collect(output);

const tags = `<link rel="manifest" href="${url('manifest.webmanifest')}">\n<meta name="theme-color" content="#315c8c">\n<link rel="apple-touch-icon" href="${url('icons/icon-192.png')}">`;
const registration = `<script>if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('${url('service-worker.js')}', { scope: '${basePath}' }).catch(console.error));</script>`;
for (const file of htmlFiles) {
  let html = fs.readFileSync(file, 'utf8');
  if (!html.includes('manifest.webmanifest')) html = html.replace('</head>', `${tags}\n</head>`);
  if (!html.includes('serviceWorker.register')) html = html.replace('</body>', `${registration}\n</body>`);
  fs.writeFileSync(file, html);
}

console.log(`PWA assets installed in _build/html for scope ${basePath}`);
