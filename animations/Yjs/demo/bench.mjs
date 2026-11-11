// bench.mjs: replay a real-world editing trace on a CRDT library. Prints one JSON object.
//
//   node bench.mjs <path/to/editing-trace.js> <trace|yjs|automerge|loro>
//
// The trace is the keystroke-by-keystroke history of a real research paper
// (Kleppmann & Beresford, "A Conflict-Free Replicated JSON Datatype", published by
// the authors in automerge/automerge-perf under CC BY 4.0): 259,778 single-character
// insertions and deletions. The file is parsed as DATA here, never imported or run.
//
// Every edit is its own transaction / change / commit, exactly as when someone types
// live and each keystroke is synced. Timings are wall-clock on the machine that runs
// this script; the film states the library versions next to them.
import { readFileSync } from 'node:fs'

const [, , tracePath, which] = process.argv
const src = readFileSync(tracePath, 'utf8')
const a = src.indexOf('const edits = [') + 'const edits = '.length
const b = src.indexOf('];\nconst finalText = ')
const edits = JSON.parse(src.slice(a, b + 1))
const finalText = JSON.parse(src.slice(b + '];\nconst finalText = '.length, src.lastIndexOf('";') + 1))
const version = (pkg) => JSON.parse(readFileSync(new URL(`./node_modules/${pkg}/package.json`, import.meta.url))).version

const t0 = performance.now()
let out

if (which === 'trace') {
  // facts about the trace itself + the document length over time (for the film's chart)
  const POINTS = 420
  const step = Math.ceil(edits.length / POINTS)
  const series = []
  let len = 0, inserts = 0, deletes = 0, peak = 0
  edits.forEach((e, i) => {
    if (e[1]) { len -= e[1]; deletes += e[1] }
    if (e.length === 3) { len += e[2].length; inserts += e[2].length }
    if (len > peak) peak = len
    if ((i + 1) % step === 0 || i === edits.length - 1) series.push([i + 1, len])
  })
  out = { edits: edits.length, inserts, deletes, final_chars: finalText.length, peak_chars: peak, length_series: series, first_line: finalText.split('\n')[0] }
} else if (which === 'yjs') {
  const Y = await import('yjs')
  const doc = new Y.Doc()
  const t = doc.getText('text')
  let wire = 0, msgs = 0
  doc.on('update', (u) => { wire += u.length; msgs++ })
  for (const e of edits) {
    if (e[1]) t.delete(e[0], e[1])
    if (e.length === 3) t.insert(e[0], e[2])
  }
  const ms = performance.now() - t0
  const ok = t.toString() === finalText
  const structs = [...doc.store.clients.values()].reduce((s, arr) => s + arr.length, 0)
  let live = 0, dead = 0
  for (let it = t._start; it; it = it.right) { if (it.deleted) dead++; else live++ }
  const bytesV1 = Y.encodeStateAsUpdate(doc)
  const bytesV2 = Y.encodeStateAsUpdateV2(doc)
  const t2 = performance.now()
  const d2 = new Y.Doc(); Y.applyUpdateV2(d2, bytesV2)
  const loadMs = performance.now() - t2
  out = { version: version('yjs'), ms, ok, structs, live_items: live, tombstone_items: dead, bytes: bytesV2.length, bytes_v1: bytesV1.length, load_ms: loadMs, load_ok: d2.getText('text').toString() === finalText, wire_bytes: wire, wire_msgs: msgs }
} else if (which === 'automerge') {
  const A = await import('@automerge/automerge')
  let doc = A.from({ text: '' })
  for (const e of edits) {
    doc = A.change(doc, (d) => { A.splice(d, ['text'], e[0], e[1], e.length === 3 ? e[2] : '') })
  }
  const ms = performance.now() - t0
  const ok = doc.text === finalText
  const bytes = A.save(doc)
  const t2 = performance.now()
  const d2 = A.load(bytes)
  const loadMs = performance.now() - t2
  out = { version: version('@automerge/automerge'), ms, ok, bytes: bytes.length, load_ms: loadMs, load_ok: d2.text === finalText }
} else if (which === 'loro') {
  const { LoroDoc } = await import('loro-crdt')
  const doc = new LoroDoc()
  const t = doc.getText('text')
  for (const e of edits) {
    if (e[1]) t.delete(e[0], e[1])
    if (e.length === 3) t.insert(e[0], e[2])
    doc.commit()
  }
  const ms = performance.now() - t0
  const ok = t.toString() === finalText
  const bytes = doc.export({ mode: 'snapshot' })
  const t2 = performance.now()
  const d2 = new LoroDoc(); d2.import(bytes)
  const s2 = d2.getText('text').toString()
  const loadMs = performance.now() - t2
  out = { version: version('loro-crdt'), ms, ok, bytes: bytes.length, load_ms: loadMs, load_ok: s2 === finalText }
} else {
  throw new Error(`unknown engine ${which}`)
}
console.log(JSON.stringify({ engine: which, node: process.version, ...out }))
