#!/usr/bin/env node
// Static analysis of Vue 3 single-file components for performance and reuse issues.
// Usage: node analyze.mjs <client-dir> [--json]
// Resolves @vue/compiler-sfc from <client-dir>/node_modules, so it needs no install of its own.
// Read-only: it never writes to the project.
import fs from 'fs'
import path from 'path'
import { createRequire } from 'module'

const clientDir = path.resolve(process.argv[2] || '.')
const asJson = process.argv.includes('--json')
const require = createRequire(path.join(clientDir, 'package.json'))
let sfc
try {
  sfc = require('@vue/compiler-sfc')
} catch {
  console.error(`Cannot load @vue/compiler-sfc from ${clientDir}/node_modules — run npm install in the client first.`)
  process.exit(2)
}

const srcDir = path.join(clientDir, 'src')
const files = []
const walk = d => {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    const p = path.join(d, e.name)
    if (e.isDirectory() && e.name !== 'node_modules') walk(p)
    else if (e.name.endsWith('.vue')) files.push(p)
  }
}
walk(srcDir)

const lineOf = (text, idx) => text.slice(0, idx).split('\n').length
const findings = []
const add = (file, line, rule, severity, message) =>
  findings.push({ file: path.relative(clientDir, file), line, rule, severity, message })

// Collect style rules per component to detect copy-pasted CSS across files
const styleBlocks = new Map()
const metrics = []

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8')
  const { descriptor, errors } = sfc.parse(text, { filename: file })
  if (errors.length) { add(file, 1, 'parse-error', 'high', String(errors[0].message || errors[0])); continue }

  const tpl = descriptor.template?.content || ''
  const tplStart = descriptor.template ? lineOf(text, descriptor.template.loc.start.offset) - 1 : 0
  const script = descriptor.scriptSetup || descriptor.script
  const js = script?.content || ''
  const jsStart = script ? lineOf(text, script.loc.start.offset) - 1 : 0
  const tplLines = tpl.split('\n').length
  const jsLines = js.split('\n').length
  const css = descriptor.styles.map(s => s.content).join('\n')
  metrics.push({ file: path.relative(clientDir, file), templateLines: tplLines, scriptLines: jsLines, styleLines: css.split('\n').length, api: descriptor.scriptSetup ? 'script-setup' : /setup\s*\(/.test(js) ? 'setup()' : 'options' })

  // --- Size / extraction (client/CLAUDE.md thresholds) ---
  if (tplLines > 100) add(file, tplStart + 1, 'large-template', 'medium', `Template is ${tplLines} lines (> 100): extract child components`)
  if (jsLines > 150) add(file, jsStart + 1, 'large-script', 'medium', `Script is ${jsLines} lines (> 150): move logic into composables`)

  // --- v-for keys ---
  for (const m of tpl.matchAll(/v-for="\(\s*\w+\s*,\s*(\w+)\s*\)\s+in[^"]*"[^>]*?:key="\1"/g))
    add(file, tplStart + lineOf(tpl, m.index), 'index-key', 'high', `v-for uses the index "${m[1]}" as :key — use a stable id`)
  for (const m of tpl.matchAll(/<[^>]*\sv-for="[^"]*"[^>]*>/g))
    if (!/:key=|v-bind:key=/.test(m[0]) && !/^<template\b/.test(m[0]))
      add(file, tplStart + lineOf(tpl, m.index), 'missing-key', 'high', 'v-for without :key')

  // --- v-if together with v-for on the same element ---
  for (const m of tpl.matchAll(/<[^>]*\sv-for="[^"]*"[^>]*>/g))
    if (/\sv-if=/.test(m[0])) add(file, tplStart + lineOf(tpl, m.index), 'v-if-with-v-for', 'medium', 'v-if on the same element as v-for — filter in a computed instead')

  // --- Function calls in template bindings (re-run every render) ---
  const callCounts = {}
  // Only render-time expressions: {{ }} interpolations and :bound attributes.
  // Event handlers (@click="fn()") run on interaction, not on every render, so they are excluded.
  for (const m of tpl.matchAll(/(?:\{\{|\s:[\w-]+=")[^"}]*?\b([a-z]\w*)\(/g)) {
    const fn = m[1]
    if (['t', '$t', 'translateProductName', 'translateWarehouse', 'translateCustomerName', 'toFixed', 'toLocaleString', 'toUpperCase', 'toLowerCase'].includes(fn)) continue
    callCounts[fn] = (callCounts[fn] || 0) + 1
  }
  for (const [fn, n] of Object.entries(callCounts))
    if (n >= 3) add(file, tplStart + 1, 'template-method-calls', 'low', `${fn}() is called ${n}× in the template — if it derives data, make it a computed or precompute per row`)

  // --- Inline styles / hardcoded colors ---
  const inlineStyles = [...tpl.matchAll(/\sstyle="/g)].length
  if (inlineStyles >= 3) add(file, tplStart + 1, 'inline-styles', 'low', `${inlineStyles} inline style="" attributes — move to classes`)
  const hex = [...(css + tpl).matchAll(/#[0-9a-fA-F]{3,8}\b/g)].length
  if (hex) add(file, 1, 'hardcoded-colors', 'low', `${hex} raw hex colors — use design tokens (src/styles/tokens.css)`)

  // --- Script: lifecycle hygiene, debug output, direct HTTP ---
  const listeners = (js.match(/addEventListener\(/g) || []).length
  const removals = (js.match(/removeEventListener\(/g) || []).length
  if (listeners > removals) add(file, jsStart + 1, 'listener-leak', 'high', `${listeners} addEventListener vs ${removals} removeEventListener — remove in onBeforeUnmount`)
  const timers = (js.match(/set(Interval|Timeout)\(/g) || []).length
  if (/setInterval\(/.test(js) && !/clearInterval\(/.test(js)) add(file, jsStart + 1, 'interval-leak', 'high', 'setInterval without clearInterval')
  for (const m of js.matchAll(/console\.(log|debug)\(/g)) add(file, jsStart + lineOf(js, m.index), 'console-log', 'low', 'console.log left in component')
  for (const m of js.matchAll(/axios\.(get|post|put|patch|delete)\(|fetch\(/g)) add(file, jsStart + lineOf(js, m.index), 'direct-http', 'medium', 'Direct HTTP call — go through src/api.js')
  for (const m of js.matchAll(/https?:\/\/localhost:\d+/g)) add(file, jsStart + lineOf(js, m.index), 'hardcoded-url', 'medium', 'Hardcoded backend URL')
  for (const m of js.matchAll(/watch\(\s*\[[^\]]*\]\s*,\s*\(\)\s*=>\s*\{?\s*(\w+)\(/g)) {
    // A watch that reloads data on every filter change is fine; flag only if the same loader is also called on mount AND immediate:true is used
    if (/immediate:\s*true/.test(js) && new RegExp(`onMounted\\([^)]*${m[1]}`).test(js))
      add(file, jsStart + lineOf(js, m.index), 'double-load', 'medium', `${m[1]}() runs from onMounted and an immediate watch — data loads twice`)
  }
  // Deep watch on large arrays
  for (const m of js.matchAll(/deep:\s*true/g)) add(file, jsStart + lineOf(js, m.index), 'deep-watch', 'low', 'deep watch — prefer watching specific fields')

  // Mixed API styles (CLAUDE.md: Composition API throughout)
  if (descriptor.script && /\bdata\s*\(\)\s*\{|\bmethods\s*:\s*\{|\bcomputed\s*:\s*\{/.test(descriptor.script.content))
    add(file, jsStart + 1, 'options-api', 'medium', 'Options API (data/methods/computed) — project standard is Composition API')

  // Loading / error states for components that fetch
  if (/api\.\w+\(/.test(js) && !/loading/.test(js)) add(file, jsStart + 1, 'no-loading-state', 'medium', 'Fetches data but has no loading state')
  if (/api\.\w+\(/.test(js) && !/error/.test(js)) add(file, jsStart + 1, 'no-error-state', 'medium', 'Fetches data but has no error state')

  // Duplicate helpers that probably belong in a shared util/composable
  for (const m of js.matchAll(/const\s+(format\w+|get\w+Class|translate\w+)\s*=\s*\(/g)) {
    styleBlocks.set('fn:' + m[1], [...(styleBlocks.get('fn:' + m[1]) || []), path.relative(clientDir, file)])
  }
  // Repeated CSS rule bodies across files
  for (const m of css.matchAll(/([^{}]+)\{([^{}]+)\}/g)) {
    const body = m[2].replace(/\s+/g, ' ').trim()
    if (body.split(';').filter(Boolean).length < 4) continue
    styleBlocks.set('css:' + body, [...(styleBlocks.get('css:' + body) || []), path.relative(clientDir, file) + ' ' + m[1].trim().slice(0, 40)])
  }
}

// Cross-file duplication
for (const [key, where] of styleBlocks) {
  const uniqueFiles = [...new Set(where.map(w => w.split(' ')[0]))]
  if (uniqueFiles.length < 2) continue
  if (key.startsWith('fn:'))
    findings.push({ file: uniqueFiles.join(', '), line: 0, rule: 'duplicate-helper', severity: 'medium', message: `${key.slice(3)}() is defined in ${uniqueFiles.length} components — move to src/utils or a composable` })
  else
    findings.push({ file: uniqueFiles.join(', '), line: 0, rule: 'duplicate-css', severity: 'low', message: `Identical CSS block in ${uniqueFiles.length} files (${where.slice(0, 3).join('; ')}) — move to a shared stylesheet` })
}

// Static route imports (no code-splitting)
const mainJs = path.join(srcDir, 'main.js')
if (fs.existsSync(mainJs)) {
  const m = fs.readFileSync(mainJs, 'utf8')
  const staticViews = [...m.matchAll(/import\s+(\w+)\s+from\s+'\.\/views\/\w+\.vue'/g)].map(x => x[1])
  if (staticViews.length > 3)
    findings.push({ file: 'src/main.js', line: 0, rule: 'no-route-splitting', severity: 'medium', message: `${staticViews.length} views imported statically — use () => import('./views/X.vue') for lazy routes` })
}

const order = { high: 0, medium: 1, low: 2 }
findings.sort((a, b) => order[a.severity] - order[b.severity] || a.file.localeCompare(b.file) || a.line - b.line)

if (asJson) {
  console.log(JSON.stringify({ components: metrics.length, metrics, findings }, null, 2))
} else {
  console.log(`Analyzed ${metrics.length} components in ${path.relative(process.cwd(), srcDir) || srcDir}\n`)
  console.log('Size (template / script / style lines, API style):')
  for (const m of metrics.sort((a, b) => b.templateLines + b.scriptLines - (a.templateLines + a.scriptLines)))
    console.log(`  ${m.file.padEnd(42)} ${String(m.templateLines).padStart(4)} / ${String(m.scriptLines).padStart(4)} / ${String(m.styleLines).padStart(4)}  ${m.api}`)
  const counts = findings.reduce((c, f) => ((c[f.severity] = (c[f.severity] || 0) + 1), c), {})
  console.log(`\nFindings: ${findings.length} (high ${counts.high || 0}, medium ${counts.medium || 0}, low ${counts.low || 0})`)
  for (const f of findings) console.log(`  [${f.severity}] ${f.rule.padEnd(22)} ${f.file}${f.line ? ':' + f.line : ''}  ${f.message}`)
}
