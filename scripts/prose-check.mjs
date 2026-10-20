#!/usr/bin/env node
// Commit gate for prose: reads markdown paths (one per line) on stdin, prints every STE finding
// as path:line: category: text, and exits 1 if there is any. repo-check.py picks the files.
// Usage: git ls-files "*.md" | node scripts/prose-check.mjs [--mode strict|flavored]
import { readFileSync } from "node:fs";
import { analyze } from "./prose-score.mjs";

const argv = process.argv.slice(2);
const modeIndex = argv.indexOf("--mode");
const mode = modeIndex !== -1 ? argv[modeIndex + 1] : "flavored";
const paths = readFileSync(0, "utf8").split(/\r?\n/).map((p) => p.trim()).filter(Boolean);

let findings = 0;
let words = 0;
for (const path of paths) {
  const r = analyze(readFileSync(path, "utf8"), { mode });
  words += r.words;
  for (const v of r.violations.sort((a, b) => a.line - b.line)) {
    findings++;
    process.stdout.write(`${path}:${v.line}: ${v.category}: ${v.text}\n`);
  }
}
process.stdout.write(`${paths.length} files, ${words} words, ${findings} findings (mode ${mode})\n`);
process.exit(findings ? 1 : 0);
