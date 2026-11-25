import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
const require = createRequire(import.meta.url);
let ts;
try { ts = require('typescript'); }
catch { ts = require('/opt/nvm/versions/node/v22.16.0/lib/node_modules/typescript/lib/typescript.js'); }
const root = path.resolve('src');
let count = 0;
const errors = [];
function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const fn = path.join(dir, name);
    const stat = fs.statSync(fn);
    if (stat.isDirectory()) { walk(fn); continue; }
    if (!/\.(jsx|js)$/.test(fn)) continue;
    const output = ts.transpileModule(fs.readFileSync(fn, 'utf8'), {
      fileName: fn,
      compilerOptions: {jsx: ts.JsxEmit.React, module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020},
      reportDiagnostics: true
    });
    for (const d of output.diagnostics || []) {
      if (d.category === ts.DiagnosticCategory.Error) {
        const pos = d.file && d.start !== undefined ? d.file.getLineAndCharacterOfPosition(d.start) : null;
        errors.push({file: fn, line: pos ? pos.line + 1 : 0, error: ts.flattenDiagnosticMessageText(d.messageText, ' ')});
      }
    }
    count++;
  }
}
walk(root);
console.log(`JSX/JS files checked: ${count}; parse errors: ${errors.length}`);
if (errors.length) { console.error(errors); process.exit(1); }
