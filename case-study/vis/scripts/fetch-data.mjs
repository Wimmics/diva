// Precomputes the SPARQL results of every competency question with Corese-Command and writes
// them to public/api/ (committed to the repo). Only needed when the data, the ontology or the
// queries change; the app itself never needs Corese.
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const out = path.join(here, 'public/api');
const queriesDir = path.join(here, '../sparql-examples');
const config = JSON.parse(fs.readFileSync(path.join(here, 'config.json'), 'utf-8'));

// CORESE_JAR points to the standalone jar; otherwise the `corese` command must be on the PATH
const [bin, ...binArgs] = process.env.CORESE_JAR ? ['java', '-jar', process.env.CORESE_JAR] : ['corese'];
const inputs = [
    path.join(here, '../data/output'),
    path.join(here, '../../ontology/diva.ttl'),
    path.join(here, '../../ontology/thesaurus.ttl'),
    'https://www.w3.org/ns/prov-o',
    'https://www.w3.org/ns/dcat3.ttl',
];

fs.rmSync(out, { recursive: true, force: true });
for (const d of ['results', 'config', 'query']) fs.mkdirSync(path.join(out, d), { recursive: true });

fs.writeFileSync(path.join(out, 'queries.json'),
    JSON.stringify(config.map(({ label, queryFile }) => ({ label, queryFile }))));

for (const q of config) {
    const file = path.join(queriesDir, q.queryFile);
    const args = [...binArgs, 'query', ...inputs.flatMap(i => ['-i', i]), '-if', 'ttl', '-of', 'json', '-q', file];
    console.log(`Running ${q.queryFile}`);
    // Corese may print log lines on stdout before the JSON
    const stdout = execFileSync(bin, args, { maxBuffer: 1024 * 1024 * 100, encoding: 'utf-8' });
    fs.writeFileSync(path.join(out, 'results', `${q.queryFile}.json`), JSON.stringify(JSON.parse(stdout.slice(stdout.search(/^\{/m)))));
    fs.writeFileSync(path.join(out, 'config', `${q.queryFile}.json`), JSON.stringify(q));
    fs.copyFileSync(file, path.join(out, 'query', q.queryFile));
}
console.log('Wrote', out);
