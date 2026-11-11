// story.mjs: the film's story, run on REAL Yjs. Prints one JSON document on stdout.
//
// Three replicas (Ada = client 1, Bob = client 2, Agent = client 3) edit one Y.Text:
//
//   1. Ada types "CRT" (three keystrokes, merged by Yjs into ONE item).
//   2. Concurrently Ada inserts "D" at index 2 and Bob inserts "s" at index 3.
//   3. Concurrently, at the SAME position, Ada types " merge edits" and the Agent
//      types " in any order".
//   4. Bob goes offline and types ", even offline". Meanwhile the Agent inserts
//      "all " and Ada deletes " in any order".
//   5. Bob reconnects: both sides exchange state vectors and send only the diff.
//
// Then the eight updates of that story are delivered to a fresh replica in EVERY
// possible order (8! = 40,320) and, separately, three times each in random order.
//
// Client ids are random 32-bit numbers in real life; they are pinned to 1, 2, 3
// here so the film can print them. Nothing else is staged.
import { readFileSync } from 'node:fs'
import * as Y from 'yjs'

const version = (pkg) => JSON.parse(readFileSync(new URL(`./node_modules/${pkg}/package.json`, import.meta.url))).version
const hex = (u8) => Array.from(u8, (b) => b.toString(16).padStart(2, '0')).join(' ')
const mk = (id) => { const d = new Y.Doc(); d.clientID = id; return d }
const T = (d) => d.getText('t')

// every character ever inserted, by id, so a tombstone can still show its old text
const CHARS = new Map()
const remember = (update) => {
  for (const s of Y.decodeUpdate(update).structs) {
    if (s.content && typeof s.content.str === 'string') {
      [...s.content.str].forEach((ch, i) => CHARS.set(`${s.id.client}:${s.id.clock + i}`, ch))
    }
  }
}
const idOf = (id) => (id ? [id.client, id.clock] : null)

function items(doc) {
  const out = []
  for (let it = T(doc)._start; it; it = it.right) {
    const str = typeof it.content.str === 'string'
      ? it.content.str
      : Array.from({ length: it.length }, (_, i) => CHARS.get(`${it.id.client}:${it.id.clock + i}`) ?? '?').join('')
    out.push({ id: idOf(it.id), len: it.length, origin: idOf(it.origin), right: idOf(it.rightOrigin), deleted: it.deleted, str })
  }
  return out
}
const sv = (doc) => Object.fromEntries(Y.decodeStateVector(Y.encodeStateVector(doc)))
const ds = (doc) => Object.fromEntries(
  [...Y.createDeleteSetFromStructStore(doc.store).clients].map(([c, a]) => [c, a.map((x) => [x.clock, x.len])]),
)
const snap = (doc) => ({
  text: T(doc).toString(),
  items: items(doc),
  sv: sv(doc),
  ds: ds(doc),
  structs: Object.fromEntries([...doc.store.clients].map(([c, a]) => [c, a.length])),
})
const describe = (key, by, update) => {
  const dec = Y.decodeUpdate(update)
  return {
    key,
    by,
    bytes: update.length,
    hex: hex(update),
    structs: dec.structs.map((s) => ({ id: idOf(s.id), len: s.length, origin: idOf(s.origin), right: idOf(s.rightOrigin), str: s.content?.str ?? null })),
    ds: Object.fromEntries([...dec.ds.clients].map(([c, a]) => [c, a.map((x) => [x.clock, x.len])])),
  }
}

// ---- the three replicas ----------------------------------------------------------
const ada = mk(1), bob = mk(2), agent = mk(3)
const log = []
for (const d of [ada, bob, agent]) d.on('update', (u, origin) => { if (origin !== 'remote') { log.push(u); remember(u) } })
const last = () => log[log.length - 1]
const deliver = (u, ...to) => to.forEach((d) => Y.applyUpdate(d, u, 'remote'))
const snaps = {}
const U = {} // the eight updates of the story, by key

// 1. Ada types C, R, T: three keystrokes
const keystrokes = []
for (const [i, ch] of [...'CRT'].entries()) {
  T(ada).insert(i, ch)
  keystrokes.push({ bytes: last().length, after: snap(ada) })
}
U.crt = Y.mergeUpdates(log.slice(0, 3))
deliver(U.crt, bob, agent)
snaps.crt = { ada: snap(ada), bob: snap(bob) }

// 2. concurrent: Ada inserts D at index 2, Bob inserts s at index 3
T(ada).insert(2, 'D'); U.d = last()
T(bob).insert(3, 's'); U.s = last()
snaps.concurrent_local = { ada: snap(ada), bob: snap(bob) }
deliver(U.s, ada, agent); deliver(U.d, bob, agent)
snaps.concurrent_merged = { ada: snap(ada), bob: snap(bob), agent: snap(agent) }

// 3. same position: Ada and the Agent both type right after "CRDTs"
T(ada).insert(5, ' merge edits'); U.merge = last()
T(agent).insert(5, ' in any order'); U.order = last()
snaps.samespot_local = { ada: snap(ada), agent: snap(agent) }
deliver(U.order, ada, bob); deliver(U.merge, agent, bob)
snaps.samespot_merged = { ada: snap(ada), bob: snap(bob), agent: snap(agent) }

// 4. Bob is offline. He keeps typing; so do the others.
T(bob).insert(T(bob).length, ', even offline'); U.offline = last()
T(agent).insert(T(agent).toString().indexOf('edits'), 'all '); U.all = last()
deliver(U.all, ada)
T(ada).delete(T(ada).toString().indexOf(' in any order'), ' in any order'.length); U.del = last()
deliver(U.del, agent)
snaps.offline = { bob: snap(bob), online: snap(ada), agent: snap(agent) }

// 5. Bob reconnects: state vectors first, then only the missing structs
const svBob = Y.encodeStateVector(bob), svOnline = Y.encodeStateVector(ada)
const toBob = Y.encodeStateAsUpdate(ada, svBob)
const toOnline = Y.encodeStateAsUpdate(bob, svOnline)
const handshake = {
  sv_bob: sv(bob),
  sv_online: sv(ada),
  sv_bob_bytes: svBob.length,
  sv_online_bytes: svOnline.length,
  to_bob: describe('to_bob', 0, toBob),
  to_online: describe('to_online', 0, toOnline),
  full_state_bytes_before: Y.encodeStateAsUpdate(ada).length,
}
deliver(toBob, bob); deliver(toOnline, ada, agent)
snaps.final = { ada: snap(ada), bob: snap(bob), agent: snap(agent) }
const FINAL = T(ada).toString()
const converged = [ada, bob, agent].every((d) => T(d).toString() === FINAL)
const fullState = Y.encodeStateAsUpdate(ada)

const by = { crt: 1, d: 1, s: 2, merge: 1, order: 3, offline: 2, all: 3, del: 1 }
const ORDER = ['crt', 'd', 's', 'merge', 'order', 'all', 'del', 'offline'] // as it happened
const updates = ORDER.map((k) => describe(k, by[k], U[k]))

// ---- every delivery order ---------------------------------------------------------
// which of the story's updates a replica has fully applied (the rest are waiting)
const appliedIn = (d, got) => {
  const have = sv(d), del = ds(d)
  return got.filter((k) => {
    const u = updates.find((x) => x.key === k)
    const structsOk = u.structs.every((s) => (have[s.id[0]] ?? 0) >= s.id[1] + s.len)
    const dsOk = Object.entries(u.ds).every(([c, ranges]) => ranges.every(([clock, len]) =>
      (del[c] ?? []).some(([c0, l0]) => c0 <= clock && clock + len <= c0 + l0)))
    return structsOk && dsOk
  })
}
// all permutations of ORDER, in lexicographic order of "as it happened" positions
function* perms(rest, head = []) {
  if (rest.length === 0) { yield head; return }
  for (let i = 0; i < rest.length; i++) {
    yield* perms([...rest.slice(0, i), ...rest.slice(i + 1)], [...head, rest[i]])
  }
}
const t0 = performance.now()
const texts = new Set(), states = new Set()
let count = 0, neededPending = 0
let waited = '' // per order: how many of the 8 updates had to wait at some point (0..7)
for (const p of perms(ORDER)) {
  const d = new Y.Doc()
  const late = new Set()
  const got = []
  let pending = false
  for (const k of p) {
    Y.applyUpdate(d, U[k])
    got.push(k)
    if (d.store.pendingStructs || d.store.pendingDs) {
      pending = true
      const ok = new Set(appliedIn(d, got))
      for (const g of got) if (!ok.has(g)) late.add(g)
    }
  }
  if (pending) neededPending++
  waited += late.size
  texts.add(T(d).toString())
  states.add(hex(Y.encodeStateAsUpdate(d)))
  count++
}
const permMs = performance.now() - t0

// ---- duplicates: every update delivered three times, in random order ---------------
let seed = 7
const rnd = () => { seed = (seed * 1103515245 + 12345) & 0x7fffffff; return seed / 0x7fffffff }
const dupTexts = new Set()
const DUP_TRIALS = 20000, DUP_COPIES = 3
for (let t = 0; t < DUP_TRIALS; t++) {
  const bag = Array.from({ length: DUP_COPIES }, () => ORDER).flat()
  for (let i = bag.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [bag[i], bag[j]] = [bag[j], bag[i]] }
  const d = new Y.Doc()
  for (const k of bag) Y.applyUpdate(d, U[k])
  dupTexts.add(T(d).toString())
}

// ---- three delivery orders the film shows step by step ------------------------------
function trace(order) {
  const d = new Y.Doc(); d.clientID = 99
  const steps = []
  const got = []
  for (const k of order) {
    Y.applyUpdate(d, U[k])
    got.push(k)
    const ok = appliedIn(d, got)
    steps.push({ key: k, text: T(d).toString(), items: items(d), applied: ok, waiting: got.filter((x) => !ok.includes(x)) })
  }
  return { order, steps }
}
const traces = [
  trace(ORDER),
  trace(ORDER.slice().reverse()),
  trace(['s', 'order', 'crt', 'offline', 'd', 'del', 'merge', 'all']),
]

console.log(JSON.stringify({
  versions: { yjs: version('yjs'), node: process.version },
  peers: { 1: 'Ada', 2: 'Bob', 3: 'Agent' },
  keystrokes,
  updates,
  snaps,
  handshake,
  final: { text: FINAL, converged, chars: FINAL.length, full_state_bytes: fullState.length, update_bytes_total: updates.reduce((a, u) => a + u.bytes, 0) },
  perms: { updates: ORDER.length, count, distinct_texts: texts.size, distinct_states: states.size, needed_pending: neededPending, ms: Math.round(permMs), text: [...texts][0], order: 'lexicographic', waited },
  dups: { trials: DUP_TRIALS, copies: DUP_COPIES, distinct_texts: dupTexts.size, text: [...dupTexts][0] },
  traces,
}, null, 1))
