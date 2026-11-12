// stack.mjs: the REAL stack the film describes, end to end, in one Node process.
//
//   Tiptap editor  <->  Y.Doc  <->  HocuspocusProvider  ==ws==  Hocuspocus server  ->  database
//
// Two real Tiptap editors (Ada, Bob; rendered into jsdom) and one headless agent (a
// plain Y.Doc + HocuspocusProvider, no editor) edit the document "notes" at the same
// time. The script then cuts Bob's connection, lets both sides edit, reconnects him,
// restarts the server and reloads the document from the database. Prints one JSON
// document.
//
// The three code panels of the film (client / server / agent) are the code below.
import { readFileSync } from 'node:fs'
import { JSDOM } from 'jsdom'

// ---- a DOM for ProseMirror (only this block is test plumbing) ----------------------
const dom = new JSDOM('<!doctype html><html><body></body></html>', { pretendToBeVisual: true })
for (const k of ['window', 'document', 'Node', 'Element', 'HTMLElement', 'MutationObserver', 'DOMParser',
  'getComputedStyle', 'requestAnimationFrame', 'cancelAnimationFrame', 'Text', 'Range', 'Selection',
  'DocumentFragment', 'XMLSerializer', 'innerHeight', 'innerWidth']) {
  const v = k === 'window' ? dom.window : dom.window[k]
  if (v === undefined) continue
  const value = typeof v === 'function' && !/^[A-Z]/.test(k) ? v.bind(dom.window) : v
  Object.defineProperty(globalThis, k, { value, configurable: true, writable: true })
}
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true })

const Y = await import('yjs')
const { Editor } = await import('@tiptap/core')
const { default: StarterKit } = await import('@tiptap/starter-kit')
const { default: Collaboration } = await import('@tiptap/extension-collaboration')
const { default: CollaborationCaret } = await import('@tiptap/extension-collaboration-caret')
const { HocuspocusProvider } = await import('@hocuspocus/provider')
const { Server } = await import('@hocuspocus/server')
const { Database } = await import('@hocuspocus/extension-database')

const PORT = Number(process.argv[2] ?? 4321)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))
const version = (pkg) => JSON.parse(readFileSync(new URL(`./node_modules/${pkg}/package.json`, import.meta.url))).version
const events = []
const count = (what) => events.filter((e) => e.what === what).length

// ============================ server.js ============================================
// `db` stands in for any database (documentName -> one binary blob); it only logs.
const rows = new Map()
const db = {
  get: (name) => rows.get(name),
  set: (name, state) => { rows.set(name, state); events.push({ what: 'store', bytes: state.length }) },
}
const startServer = async () => {
  // ---- the film's server.js panel, verbatim --------------------------------------
  const storage = new Database({
    fetch: (d) => db.get(d.documentName),
    store: (d) => db.set(d.documentName, d.state),
  })
  const server = new Server({
    port: PORT,
    extensions: [storage],
    // (test plumbing, not shown: a quiet start, a short debounce so the script is
    //  fast - the default is 2000 ms - and three hooks that count events)
    quiet: true,
    debounce: 250,
    async onChange({ update }) { events.push({ what: 'onChange', bytes: update.length }) },
    async onConnect() { events.push({ what: 'onConnect' }) },
    async onDisconnect() { events.push({ what: 'onDisconnect' }) },
  })
  await server.listen()
  return server
}
const defaults = new Server({ quiet: true }).hocuspocus.configuration
let server = await startServer()

// ============================ client.js ============================================
function client(name, color, clientID) {
  // ---- the film's client.js panel (plus a DOM node and a pinned client id) --------
  const ydoc = new Y.Doc()
  ydoc.clientID = clientID // random in real life; pinned so the film can print it
  const provider = new HocuspocusProvider({
    url: `ws://127.0.0.1:${PORT}`,
    name: 'notes', document: ydoc,
  })
  const editor = new Editor({ element: document.createElement('div'), extensions: [
    StarterKit.configure({ undoRedo: false }),
    Collaboration.configure({ document: ydoc }),
    CollaborationCaret.configure({
      provider, user: { name, color },
    }),
  ] })
  return { name, ydoc, provider, editor }
}
const synced = (c) => new Promise((res) => (c.provider.isSynced ? res() : c.provider.on('synced', () => res())))
const html = (c) => c.editor.getHTML()
// position of `needle` inside the editor's document (ProseMirror position)
const posOf = (c, needle, after = false) => {
  let p = -1
  c.editor.state.doc.descendants((node, pos) => {
    if (p < 0 && node.isText && node.text.includes(needle)) p = pos + node.text.indexOf(needle) + (after ? needle.length : 0)
  })
  if (p < 0) throw new Error(`"${needle}" not found for ${c.name}`)
  return p
}
const type = async (c, at, text, gap = 4) => {
  for (const ch of text) { c.editor.commands.insertContentAt(at++, ch); await sleep(gap) }
  return at
}

const ada = client('Ada', '#508FF9', 1)
const bob = client('Bob', '#E26E1A', 2)
await Promise.all([synced(ada), synced(bob)])

// ---- 1. three writers, one page -----------------------------------------------------
ada.editor.commands.setNode('heading', { level: 1 })
await type(ada, 1, 'Release notes')
await sleep(60)
// Bob types the first paragraph (the empty one Tiptap keeps after a heading)
let bobAt = bob.editor.state.doc.content.size - 1
bobAt = await type(bob, bobAt, 'Live collaboration ships')
// Ada edits the SAME paragraph while Bob is still typing its end
const adaTyping = (async () => { await sleep(20); await type(ada, posOf(ada, 'ships'), 'finally ') })()
await sleep(30)
let tail = 0
for (const ch of ' this week.') { bob.editor.commands.insertContentAt(posOf(bob, 'ships', true) + tail++, ch); await sleep(4) }
await adaTyping
await sleep(80)
const afterHumans = { ada: html(ada), bob: html(bob) }

// ============================ agent.js =============================================
// The agent is one more peer: its own Y.Doc, its own provider, its own client id.
const tokens = ['Summary:', ' we', ' all', ' edit', ' at', ' once', ' and', ' stay', ' in', ' sync', '.']
let bobEdit = null
// stands in for an LLM token stream; Bob edits inside the agent's sentence mid-stream
async function* llm() {
  for (const [i, token] of tokens.entries()) {
    yield token
    await sleep(12)
    if (i === 6) bobEdit = (async () => { await type(bob, posOf(bob, ' all') + 1, 'can ') })()
  }
}
const stream = llm()
const me = { name: 'Agent', color: '#C170BB' }
let provider
const write = (ydoc, token) => {
  const body = ydoc.getXmlFragment('default')
  if (!write.text) { // the agent's own paragraph, created on its first token
    const paragraph = new Y.XmlElement('paragraph')
    paragraph.insert(0, [new Y.XmlText()])
    body.push([paragraph])
    write.text = paragraph.get(0)
  }
  const text = write.text
  text.insert(text.length, token) // a plain Yjs insert
  const here = Y.relativePositionToJSON(Y.createRelativePositionFromTypeIndex(text, text.length))
  provider.setAwarenessField('cursor', { anchor: here, head: here }) // the agent's caret
}
// ---- the film's agent.js panel, verbatim (plus a pinned client id) ------------------
const agentDoc = await (async () => {
  const ydoc = new Y.Doc()
  ydoc.clientID = 3
  provider = new HocuspocusProvider({
    url: `ws://127.0.0.1:${PORT}`,
    name: 'notes', document: ydoc,
  })
  provider.setAwarenessField('user', me)
  await synced({ provider })

  for await (const token of stream) {
    write(ydoc, token) // a plain Yjs insert
  }
  return ydoc
})()
const agentProvider = provider
const body = agentDoc.getXmlFragment('default')
await bobEdit
await sleep(150)
const serverXml = () => server.hocuspocus.documents.get('notes').getXmlFragment('default').toString()
const afterAgent = { ada: html(ada), bob: html(bob), agent_xml: body.toString(), server_xml: serverXml() }
const awareness = [...ada.provider.awareness.getStates()].map(([clientId, s]) => ({ clientId, user: s.user ?? null, has_cursor: !!s.cursor }))
const caretLabels = [...ada.editor.view.dom.querySelectorAll('.collaboration-carets__label')].map((n) => n.textContent)

// ---- 2. Bob loses his connection, both sides keep editing, Bob comes back -------------
bob.provider.disconnect()
await sleep(120)
await type(bob, posOf(bob, 'notes', true), ' (draft)')
await type(ada, posOf(ada, 'sync', true), ', even offline')
await sleep(120)
const whileOffline = { ada: html(ada), bob: html(bob) }
await bob.provider.connect()
await sleep(700)
const afterReconnect = { ada: html(ada), bob: html(bob), server_xml: serverXml() }

// ---- 3. the server restarts: the document comes back from the database -----------------
await sleep(400) // let the debounced store run
const storedBytes = rows.get('notes').length
const stateBytes = Y.encodeStateAsUpdate(ada.ydoc).length
ada.editor.destroy(); bob.editor.destroy(); ada.provider.destroy(); bob.provider.destroy(); agentProvider.destroy()
await server.destroy()
await sleep(150)
server = await startServer()
const carol = client('Carol', '#2EC4B6', 4)
await synced(carol)
await sleep(150)
const afterRestart = html(carol)
carol.editor.destroy(); carol.provider.destroy()
await server.destroy()

console.log(JSON.stringify({
  versions: {
    node: process.version,
    yjs: version('yjs'),
    tiptap: version('@tiptap/core'),
    hocuspocus: version('@hocuspocus/server'),
    y_tiptap: version('@tiptap/y-tiptap'),
  },
  defaults: { debounce: defaults.debounce, maxDebounce: defaults.maxDebounce, timeout: defaults.timeout, gc: defaults.yDocOptions.gc },
  client_ids: { ada: ada.ydoc.clientID, bob: bob.ydoc.clientID, agent: agentDoc.clientID },
  tokens,
  after_humans: afterHumans,
  after_agent: afterAgent,
  awareness,
  caret_labels_in_ada_editor: caretLabels,
  while_offline: whileOffline,
  after_reconnect: afterReconnect,
  after_restart: afterRestart,
  stored_bytes: storedBytes,
  state_bytes: stateBytes,
  events: { onConnect: count('onConnect'), onDisconnect: count('onDisconnect'), onChange: count('onChange'), store: count('store'), onChange_bytes: events.filter((e) => e.what === 'onChange').map((e) => e.bytes) },
}, null, 1))
process.exit(0)
