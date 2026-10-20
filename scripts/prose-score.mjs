#!/usr/bin/env node
// Deterministic prose scorer, based on ASD-STE100 Simplified Technical English (rules paraphrased,
// no dictionary). Score = violations per 100 words; 0.00 is clean. prose-check.mjs gates commits on it.
// Silence one category in a file: <!-- prose-score-disable: passive-voice -->
// Usage: node scripts/prose-score.mjs <file> [--mode strict|flavored] [--detail]
// Node standard library only. No model call. Same input -> same score.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

// v2 (2026-08-02): added ing-main-verb. Scores are NOT comparable with v1 numbers.
// v3 (2026-08-08): added ste-banned-word, marketing-adjective, phrasal-verb-slop.
// Scores are NOT comparable with v2 numbers.
export const RULESET_VERSION = "3";

const IRREGULAR = "done|made|seen|taken|given|written|known|shown|found|held|kept|left|sent|built|brought|bought|caught|taught|thought|told|sold|put|set|cut|read|run|come|become|begun|chosen|driven|eaten|fallen|forgotten|gotten|hidden|broken|spoken|stolen|drawn|grown|thrown|blown|worn|torn|born|lost|meant|met|paid|said|laid|led|fed|felt|heard";
const CONTRACTIONS = "it's|don't|can't|won't|isn't|aren't|doesn't|didn't|we're|you're|they're|i'm|we've|they've|you've|i've|that's|there's|here's|let's|wouldn't|shouldn't|couldn't|hasn't|haven't|hadn't|wasn't|weren't|we'll|you'll|it'll|they'll|ain't|what's|who's";
const HEDGE = /\b(?:perhaps|arguably|seemingly|possibly|potentially|somewhat|relatively|presumably|ostensibly|conceivably|might)\b/gi;
// Words ending in -ing that follow "be" without forming a progressive main verb:
// pronouns, plain nouns, and participial adjectives. Without these the check is noise.
const ING_NOT_A_VERB = new Set(`something nothing anything everything morning evening during
ceiling building meaning warning opening setting string thing king ring wing spring being
interesting exciting boring willing unwilling outstanding promising confusing misleading
surprising challenging demanding compelling convincing encouraging disappointing satisfying
rewarding amazing striking puzzling worrying alarming appealing engaging missing pending
existing remaining ongoing leading corresponding according conflicting differing varying
underlying welcoming forthcoming upcoming binding lasting fitting pressing growing willing`
  .split(/\s+/).filter(Boolean));

// Categories that fire on a whole segment of prose text.
const TEXT_RULES = [
  ["slop-phrase", [
    /\bit(?:\s+is|'s)\s+(?:important|worth)\s+(?:to\s+note|noting)\b/i,
    /\bit\s+should\s+be\s+noted\b/i,
    /\bin\s+today's\s+[a-z-]+\s+(?:world|landscape|era|environment)\b/i,
    /\bin\s+an\s+era\s+of\b|\bin\s+a\s+world\s+where\b/i,
    /\bdelv(?:e|es|ing)\s+into\b/i,
    /\bat\s+the\s+end\s+of\s+the\s+day\b/i,
    /\bin\s+conclusion\b|\bto\s+summarize\b/i,
    /\bwhen\s+it\s+comes\s+to\b/i,
    /\bin\s+the\s+realm\s+of\b/i,
    /\bplays?\s+an?\s+(?:key|vital|crucial|critical|central|pivotal|significant)\s+role\b/i,
    /\bserves?\s+as\s+a\s+testament\b/i,
    /\blet's\s+(?:unpack|break\s+this\s+down|dive\s+in)\b/i,
    /\bhere's\s+(?:the\s+thing|the\s+kicker|where\s+it\s+gets)\b/i,
    /\bthe\s+key\s+takeaway\b/i,
    /\bnavigat(?:e|ing)\s+the\s+(?:complexities|landscape)\b/i,
    /\b(?:game[\s-]changer|paradigm\s+shift|double[\s-]edged\s+sword|perfect\s+storm|north\s+star|deep\s+dive)\b/i,
    /\b(?:broader|wider)\s+implications\b/i,
    /\bdespite\s+(?:these|its)\s+(?:challenges|limitations)\b/i,
    /\bi\s+hope\s+this\s+helps\b|\bgreat\s+question\b/i,
    /\bplease\s+note\s+that\b/i,
    /\bas\s+(?:mentioned|noted|stated)\s+(?:above|earlier|previously)\b/i,
  ]],
  // Bureaucratic register STE replaces with a shorter word: begin -> start,
  // ensure -> make sure, prior to -> before. Deduped against elevated-register.
  ["ste-banned-word", [
    /\b(?:begins?|initiat(?:e|es|ed)|originat(?:e|es|ed)|leverag(?:e|es|ed|ing)|ensur(?:e|es|ed|ing)|obtains?|obtained|acquir(?:e|es|ed)|demonstrat(?:e|es|ed)|comprehensive(?:ly)?|aforementioned|henceforth|therein|whilst|amongst|numerous|prior\s+to|subsequent\s+to|in\s+order\s+to|a\s+variety\s+of|in\s+the\s+event\s+that|due\s+to\s+the\s+fact\s+that)\b/gi,
  ]],
  // Enthusiasm inflation. Not an STE category — STE has no marketing copy to ban.
  // "unlock" and "first-class" are left out: both are ordinary technical terms here.
  ["marketing-adjective", [
    /\b(?:powerful|effortless(?:ly)?|world[\s-]class|next[\s-]generation|revolutionary|blazing|lightning[\s-]fast|elegant|delightful|turnkey|best[\s-]in[\s-]class|game[\s-]changing|battle[\s-]tested|enterprise[\s-]grade|supercharges?|unleash(?:es)?|empowers?)\b/gi,
  ]],
  // Vague phrasal verbs. STE approves the plain single verb: start, create, remove.
  ["phrasal-verb-slop", [
    /\b(?:spin(?:s|ning)?\s+(?:up|down)|spun\s+up|reach(?:es|ing)?\s+out|div(?:e|es|ing)\s+into|kick(?:s|ing)?\s+off|roll(?:s|ing)?\s+out|tear(?:s|ing)?\s+down|ramp(?:s|ing)?\s+up|circl(?:e|es|ing)\s+back|drill(?:s|ing)?\s+down)\b/gi,
  ]],
  ["negation-pivot", [
    /\bnot\s+(?:just|only|merely|simply)\b[^.!?]{0,60}?\b(?:but|it(?:'s|\s+is))\b/i,
    /\bis\s+not\s+[a-z]+\s*—\s*it(?:'s|\s+is)\b/i,
  ]],
  ["vague-attribution", [
    /\b(?:experts?|studies|research|scientists|analysts)\s+(?:say|says|argue|argues|show|shows|suggest|suggests|believe|believes|indicate|indicates)\b/i,
    /\bmany\s+(?:believe|argue|say|think)\b/i,
    /\bit\s+is\s+widely\s+(?:believed|accepted|known|regarded)\b/i,
  ]],
  ["elevated-register", [
    /\b(?:utiliz(?:e|es|ed|ing|ation)|commenc(?:e|es|ed)|endeavou?r|facilitat(?:e|es|ed)|delve|tapestry|myriad|plethora|pivotal|robust|seamless|crucial|holistic|paradigm|synerg(?:y|ies)|cutting[\s-]edge|state[\s-]of[\s-]the[\s-]art|transformative|unprecedented|meticulous|intricate|nuanced|realm|foster(?:s|ed|ing)?|underscor(?:e|es|ed)|showcas(?:e|es|ed)|garner(?:s|ed)?|harness(?:es|ed)?|embark|streamlin(?:e|es|ed)|spearhead(?:s|ed)?|bolster(?:s|ed)?|testament|vibrant|bustling|treasure\s+trove)\b/gi,
  ]],
  ["nominalization", [
    /\b(?:make|makes|made)\s+an?\s+(?:decision|assessment|determination)\b/i,
    /\b(?:provide|provides|provided)\s+an?\s+(?:description|explanation)\b/i,
    /\b(?:perform|performs|conduct|conducts|carry\s+out|carries\s+out)\s+an?\s+(?:analysis|investigation|evaluation|review)\b/i,
    /\b(?:take|takes|give|gives)\s+(?:into\s+)?consideration\b/i,
  ]],
];

// Categories that fire per sentence.
const SENTENCE_RULES = [
  ["filler-opener", [
    /^(?:Furthermore|Moreover|Additionally|Importantly|Ultimately|Essentially|Fundamentally|Notably|In\s+essence|That\s+said)\b/i,
  ]],
];

const STRICT_TEXT_RULES = [
  ["contraction", [new RegExp(`\\b(?:${CONTRACTIONS})\\b`, "gi")]],
  ["complex-tense", [new RegExp(`\\b(?:have|has|had)\\s+(?!been\\b)(?:\\w+ed|${IRREGULAR})\\b`, "gi")]],
  ["compound-instruction", [/,\s*then\b|\band\s+then\b/gi]],
];

const ALL_CATEGORIES = [
  "sentence-length", "paragraph-length", "passive-voice", "slop-phrase", "negation-pivot",
  "filler-opener", "vague-attribution", "hedge-stack", "em-dash-run", "nominalization",
  "elevated-register", "ing-main-verb", "contraction", "semicolon", "complex-tense",
  "compound-instruction", "ste-banned-word", "marketing-adjective", "phrasal-verb-slop",
];

const ABBREV = /(?:\b(?:e\.g|i\.e|etc|vs|Dr|Mr|Mrs|Ms|Fig|approx|Inc|Ltd|cf|al|Jr|Sr|St)\.|\b[A-Z]\.)$/;

function maskLine(raw) {
  let t = raw;
  t = t.replace(/<!--[\s\S]*?-->/g, "");
  t = t.replace(/`[^`]*`/g, " ");
  t = t.replace(/!\[[^\]]*\]\([^)]*\)/g, " ");
  t = t.replace(/\[([^\]]*)\]\([^)]*\)/g, "$1");
  t = t.replace(/<https?:\/\/[^>]*>/g, " ");
  t = t.replace(/https?:\/\/\S+/g, " ");
  t = t.replace(/^\s*>\s?/, "");
  t = t.replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "");
  t = t.replace(/^\s*#{1,6}\s+/, "");
  t = t.replace(/^\s*\*\*[^*]{1,60}?:?\*\*:?\s*/, ""); // bold label, e.g. **Label:**
  return t.trimEnd();
}

function classify(source) {
  const lines = source.split(/\r?\n/);
  const blocks = [];
  let inFence = false;
  let current = null;
  const push = () => { if (current && current.lines.length) blocks.push(current); current = null; };

  let start = 0;
  if (lines[0] !== undefined && lines[0].trim() === "---") {
    const end = lines.findIndex((l, i) => i > 0 && l.trim() === "---");
    if (end > 0) start = end + 1;
  }

  for (let i = start; i < lines.length; i++) {
    const raw = lines[i];
    const n = i + 1;
    const trimmed = raw.trim();
    if (/^(?:```|~~~)/.test(trimmed)) { inFence = !inFence; push(); continue; }
    if (inFence) continue;
    if (trimmed === "") { push(); continue; }
    if (/^\|/.test(trimmed)) {
      if (!current || current.type !== "table") { push(); current = { type: "table", lines: [] }; }
      const cells = trimmed.replace(/^\||\|$/g, "").split("|").map((c) => maskLine(c.trim()));
      if (!/^[\s|:-]+$/.test(trimmed)) current.lines.push({ n, text: cells.join(". ") });
      continue;
    }
    if (/^#{1,6}\s/.test(trimmed)) { push(); blocks.push({ type: "heading", lines: [{ n, text: maskLine(raw) }] }); continue; }
    if (/^(?:[-*+]|\d+[.)])\s/.test(trimmed)) { push(); current = { type: "listitem", lines: [{ n, text: maskLine(raw) }] }; continue; }
    if (current && current.type === "listitem") { current.lines.push({ n, text: maskLine(raw) }); continue; }
    if (!current || current.type !== "paragraph") { push(); current = { type: "paragraph", lines: [] }; }
    current.lines.push({ n, text: maskLine(raw) });
  }
  push();
  return blocks.filter((b) => b.lines.some((l) => l.text.trim() !== ""));
}

function joinBlock(block) {
  let text = "";
  const map = [];
  for (const l of block.lines) {
    if (text) { text += " "; map.push(l.n); }
    for (let k = 0; k < l.text.length; k++) map.push(l.n);
    text += l.text;
  }
  const first = block.lines[0] ? block.lines[0].n : 1;
  return { text, lineAt: (i) => map[Math.max(0, Math.min(i, map.length - 1))] ?? first };
}

function splitSentences(text) {
  const out = [];
  let buf = "";
  for (const piece of text.split(/(?<=[.!?])\s+/)) {
    buf = buf ? `${buf} ${piece}` : piece;
    if (ABBREV.test(buf.trim())) continue;
    out.push(buf);
    buf = "";
  }
  if (buf.trim()) out.push(buf);
  return out.filter((s) => s.trim() !== "");
}

const countWords = (t) => (t.match(/[A-Za-z0-9][A-Za-z0-9'’-]*/g) || []).length;
const isEars = (t) => /\bTHE\s+SYSTEM\s+SHALL\b/.test(t);

function findPassive(text) {
  const hits = [];
  const re = new RegExp(`\\b(?:is|are|was|were|be|been|being|gets|got)\\s+(?:\\w+ly\\s+)?(\\w+ed|${IRREGULAR})\\b`, "gi");
  let m;
  while ((m = re.exec(text)) !== null) {
    const after = text[m.index + m[0].length];
    const before = text[m.index - 1];
    if (after === "-" || before === "-") continue; // read-only, well-formed
    hits.push({ index: m.index, text: m[0] });
  }
  return hits;
}

function findIngMainVerb(text) {
  const hits = [];
  const re = /\b(?:am|is|are|was|were|be|been)\s+(\w+ing)\b/gi;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (ING_NOT_A_VERB.has(m[1].toLowerCase())) continue;
    const after = text[m.index + m[0].length];
    const before = text[m.index - 1];
    if (after === "-" || before === "-") continue; // is well-meaning
    hits.push({ index: m.index, text: m[0] });
  }
  return hits;
}

function findNominalization(text) {
  const hits = [];
  const re = /\b(\w{4,}(?:tion|sion|ment|ance|ence|ity))\s+of\b/gi;
  let m;
  while ((m = re.exec(text)) !== null) {
    const word = m[1];
    const atSentenceStart = m.index === 0 || /[.!?]\s+$/.test(text.slice(Math.max(0, m.index - 3), m.index));
    if (/^[A-Z]/.test(word) && !atSentenceStart) continue; // Association of Europe
    hits.push({ index: m.index, text: m[0] });
  }
  return hits;
}

function scanPatterns(text, patterns) {
  const hits = [];
  for (const p of patterns) {
    const re = new RegExp(p.source, p.flags.includes("g") ? p.flags : `${p.flags}g`);
    let m;
    while ((m = re.exec(text)) !== null) {
      hits.push({ index: m.index, text: m[0] });
      if (m[0] === "") re.lastIndex++;
    }
  }
  return hits;
}

export function analyze(source, options = {}) {
  const mode = options.mode === "strict" ? "strict" : "flavored";
  const cap = mode === "strict" ? 20 : 25;
  const suppressed = new Set();
  // A directive inside a code fence is documentation, not a directive.
  let fenced = false;
  const directiveText = source.split(/\r?\n/).filter((l) => {
    if (/^\s*(?:```|~~~)/.test(l)) { fenced = !fenced; return false; }
    return !fenced;
  }).join("\n");
  const sup = directiveText.match(/<!--\s*prose-score-disable:\s*([^>]+?)\s*-->/);
  if (sup) for (const c of sup[1].split(",")) suppressed.add(c.trim());

  const blocks = classify(source);
  const violations = [];
  let words = 0;
  const add = (line, category, text) => {
    if (suppressed.has(category)) return;
    violations.push({ line, category, text: text.trim().slice(0, 90) });
  };

  for (const block of blocks) {
    const { text, lineAt } = joinBlock(block);
    if (text.trim() === "") continue;
    words += countWords(text);
    const lengthChecked = block.type === "paragraph" || block.type === "listitem";

    const textRules = mode === "strict" ? [...TEXT_RULES, ...STRICT_TEXT_RULES] : TEXT_RULES;
    for (const [category, patterns] of textRules) {
      for (const hit of scanPatterns(text, patterns)) add(lineAt(hit.index), category, hit.text);
    }
    for (const hit of findNominalization(text)) add(lineAt(hit.index), "nominalization", hit.text);
    for (const hit of findIngMainVerb(text)) add(lineAt(hit.index), "ing-main-verb", hit.text);
    if (mode === "strict") {
      let s = text.indexOf(";");
      while (s !== -1) { add(lineAt(s), "semicolon", text.slice(Math.max(0, s - 25), s + 1)); s = text.indexOf(";", s + 1); }
    }

    let dash = text.indexOf("—");
    let dashSeen = 0;
    while (dash !== -1) {
      dashSeen += 1;
      if (dashSeen > 1) add(lineAt(dash), "em-dash-run", text.slice(Math.max(0, dash - 30), dash + 20));
      dash = text.indexOf("—", dash + 1);
    }

    const sentences = splitSentences(text);
    let offset = 0;
    for (const sentence of sentences) {
      const at = text.indexOf(sentence, offset);
      const index = at === -1 ? offset : at;
      offset = index + sentence.length;
      const line = lineAt(index);
      const trimmedSentence = sentence.trim();

      if (!isEars(trimmedSentence)) {
        for (const hit of findPassive(sentence)) add(lineAt(index + hit.index), "passive-voice", hit.text);
      }
      for (const [category, patterns] of SENTENCE_RULES) {
        if (scanPatterns(trimmedSentence, patterns).length) add(line, category, trimmedSentence);
      }
      const hedges = trimmedSentence.match(HEDGE);
      if (hedges && hedges.length >= 2) add(line, "hedge-stack", hedges.join(" + "));
      if (lengthChecked) {
        const n = countWords(trimmedSentence);
        if (n > cap) add(line, "sentence-length", `${n} words: ${trimmedSentence.slice(0, 60)}`);
      }
    }
    if (block.type === "paragraph" && sentences.length > 6) {
      add(lineAt(0), "paragraph-length", `${sentences.length} sentences in one paragraph`);
    }
  }

  const byCategory = {};
  for (const c of ALL_CATEGORIES) byCategory[c] = 0;
  for (const v of violations) byCategory[v.category] = (byCategory[v.category] || 0) + 1;
  const score = words === 0 ? 0 : (violations.length / words) * 100;

  return {
    mode, words, violations, byCategory,
    score: Math.round(score * 100) / 100,
    ruleset: RULESET_VERSION,
    suppressed: [...suppressed],
  };
}

function readInput(path) {
  if (path) return readFileSync(path, "utf8");
  if (process.stdin.isTTY) {
    process.stderr.write("usage: node scripts/prose-score.mjs <file> [--mode strict|flavored] [--detail]\n");
    process.exit(2);
  }
  try { return readFileSync(0, "utf8"); } catch { return ""; }
}

function main() {
  // Output is routinely piped to head/tail/sed, which closes stdout early. Exit quietly.
  process.stdout.on("error", (e) => { if (e.code === "EPIPE") process.exit(0); throw e; });
  const argv = process.argv.slice(2);
  const detail = argv.includes("--detail");
  const modeIndex = argv.indexOf("--mode");
  const mode = modeIndex !== -1 ? argv[modeIndex + 1] : "flavored";
  const path = argv.find((a, i) => !a.startsWith("--") && (modeIndex === -1 || i !== modeIndex + 1));
  const source = readInput(path);
  const r = analyze(source, { mode });

  const label = path || "(stdin)";
  process.stdout.write(
    `${label}\nscore ${r.score.toFixed(2)} violations per 100 words  ` +
    `(words: ${r.words}, violations: ${r.violations.length}, mode: ${r.mode}, ruleset: v${r.ruleset})\n`,
  );
  if (r.words === 0) {
    process.stdout.write("WARNING: 0 words measured. This score is meaningless, not clean.\n");
  } else if (r.words < 20) {
    process.stdout.write(`WARNING: only ${r.words} words measured. Check that this matches the input.\n`);
  }
  if (r.suppressed.length) process.stdout.write(`suppressed: ${r.suppressed.join(", ")}\n`);
  if (detail) {
    const rows = Object.entries(r.byCategory).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]);
    if (!rows.length) process.stdout.write("no findings by category\n");
    for (const [c, n] of rows) process.stdout.write(`  ${String(n).padStart(4)}  ${c}\n`);
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();
