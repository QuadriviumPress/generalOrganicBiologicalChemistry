import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import YAML from 'yaml';

const root = process.cwd();
const required = ['myst.yml', 'index.md', '.github/workflows/ci.yml', '.github/workflows/deploy.yml', 'pwa/service-worker.js'];
const missing = required.filter((file) => !fs.existsSync(path.join(root, file)));
if (missing.length) throw new Error(`Missing required files: ${missing.join(', ')}`);

const config = YAML.parse(fs.readFileSync(path.join(root, 'myst.yml'), 'utf8'));
const errors = [];
if (!config.project?.title) errors.push('project.title is required');
if (!config.project?.short_title) errors.push('project.short_title is required');
if (config.project?.open_access !== true) errors.push('project.open_access must be true');
if (!config.project?.github) errors.push('project.github is required');
if (!Array.isArray(config.project?.toc) || !config.project.toc.length) errors.push('project.toc must contain at least one page');
if (errors.length) throw new Error(errors.join('\n'));

console.log('Book structure and required MyST metadata are valid.');
