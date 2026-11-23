// Copies the texts the page shows out of the benchmark (evals/results is not in git) into cases.json.
// Run from site/ after changing a data-case or data-run in index.html: node collect-cases.mjs
import { readFileSync, writeFileSync } from 'node:fs';

const root = new URL('../evals/', import.meta.url);
const read = (path) => readFileSync(new URL(path, root), 'utf8').trim();
const html = readFileSync(new URL('index.html', import.meta.url), 'utf8');
const cases = {};

for (const [, id, run] of html.matchAll(/data-case="([^"]+)" data-run="([^"]+)"/g)) {
  const spec = JSON.parse(read(`cases/${id}.json`));
  const [results, rep] = run.split('/');
  const saved = (arm) => read(`results/${results}/runs/${id.replace('/', '__')}__omp__${arm}__${rep}/workspace/${spec.output}`);
  cases[id] = { output: spec.output, files: spec.files ?? {}, without: saved('baseline'), with: saved('skill') };
}

writeFileSync(new URL('cases.json', import.meta.url), JSON.stringify(cases, null, 1) + '\n');
console.log(`${Object.keys(cases).length} cases written to cases.json`);
