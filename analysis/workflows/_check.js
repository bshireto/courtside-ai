// Syntax-check the workflow scripts by compiling them as the body of an async function with stubbed globals.
const fs = require('fs');
const path = require('path');
for (const f of process.argv.slice(2)) {
  const src = fs.readFileSync(f, 'utf8').replace(/^export const meta/m, 'const meta');
  try {
    new Function('agent', 'parallel', 'pipeline', 'phase', 'log', 'args', 'budget', 'workflow', 'async function main(){' + src + '}');
    console.log(path.basename(f), 'syntax OK');
  } catch (e) {
    console.log(path.basename(f), 'SYNTAX ERROR', e.message);
    process.exitCode = 1;
  }
}
