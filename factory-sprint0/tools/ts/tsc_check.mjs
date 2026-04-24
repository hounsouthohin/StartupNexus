// tools/ts/tsc_check.mjs
// Usage  : node tsc_check.mjs <project_root>
// Stdout : JSON array of TypeScript error diagnostics
// Exit   : 0 (no errors), 1 (TS errors found), 2 (tsconfig absent / load failure)
//
// Replaces `npx tsc --noEmit --pretty false` + regex parsing.
// getPreEmitDiagnostics() = syntactic + semantic + declaration diagnostics,
// équivalent exact de tsc --noEmit. Pas de parsing de texte.

import { Project, ts } from 'ts-morph';
import path from 'path';
import fs from 'fs';

const projectRoot = process.argv[2];

if (!projectRoot) {
  process.stderr.write('Usage: node tsc_check.mjs <project_root>\n');
  process.exit(2);
}

const tsConfigPath = path.join(projectRoot, 'tsconfig.json');
if (!fs.existsSync(tsConfigPath)) {
  process.stderr.write(`tsconfig.json absent: ${tsConfigPath}\n`);
  process.exit(2);
}

let project;
try {
  project = new Project({
    tsConfigFilePath: tsConfigPath,
    skipAddingFilesFromTsConfig: false,
  });
} catch (err) {
  process.stderr.write(`Failed to load project: ${err.message}\n`);
  process.exit(2);
}

const diagnostics = project.getPreEmitDiagnostics();

const result = diagnostics
  .filter(d => d.getCategory() === 1) // DiagnosticCategory.Error = 1 (skip warnings/suggestions)
  .map(d => {
    const cd = d.compilerObject; // underlying ts.Diagnostic
    let filePath = null;
    let lineNum = null;
    let col = null;

    if (cd.file) {
      filePath = cd.file.fileName;
      if (cd.start != null) {
        const lc = cd.file.getLineAndCharacterOfPosition(cd.start);
        lineNum = lc.line + 1;    // 0-indexed → 1-indexed
        col     = lc.character + 1; // 0-indexed → 1-indexed
      }
    }

    return {
      file:    filePath,
      line:    lineNum,
      col:     col,
      code:    `TS${cd.code}`,
      message: ts.flattenDiagnosticMessageText(cd.messageText, ' '),
    };
  });

process.stdout.write(JSON.stringify(result));
process.exit(result.length > 0 ? 1 : 0);
