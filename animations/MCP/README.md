# MCP, the Model Context Protocol

How an AI application plugs into tools and data. A narrated, house-style Manim film
built on `manimx`: the voice carries the explanation, the screen carries the real
artifacts (the model's context, JSON-RPC messages, a function, a table) and a handful
of captions. Flat scenes, no camera.

One stage, three actors, in the order a request crosses them:

    model (its context)  |  host (the app, its user, a client)  ==wire==  server

and one question followed from end to end: "How many orders shipped late in week 46?"

## What it teaches

1. **A model alone.** A model reads its context and writes text. The answer sits in a
   table it cannot reach.
2. **One protocol.** Host, client, server. A request and its response as JSON, tied by
   an id. `tools/list`: a tool is a name, a description and a schema, built here from a
   function's signature, and it lands in the model's context.
3. **One call.** The model writes a call, the host asks the user, the client sends
   `tools/call`, the server runs its function on the table, the result comes back as
   more text, the model answers. The model never touches the database.
4. **Three doors.** Prompts (the user decides), resources (the application), tools (the
   model): three ways for a server's text to reach the same context.
5. **Anywhere.** Locally: a child process and two pipes, one line of JSON per message.
   Remotely: an HTTP POST with an access token. Since revision 2026-07-28 there is no
   handshake and no session, every request says everything, so any copy behind a load
   balancer can answer.
6. **Trust.** Three hosts and four systems are seven pieces to build, not twelve. But a
   server's descriptions are text the model reads and its tools are code that runs
   with your access: a stranger's tool carries an instruction, the user says no.
7. **The whole picture.** The stage again, each actor lit on its sentence.

Colour is identity: purple the model, blue the host and its client, orange a server
and whatever text comes from one, green the user. Gold marks the thing to look at, red
what is hostile.

## What is real, and what is not

**Nothing was captured.** By choice, no MCP client or server was run on this machine,
not even a demo one. The messages on screen are written by hand from the specification,
revision **2026-07-28**, in `wire.py`, and a note at the bottom of the screen says so.
`wire.py` checks them when it is imported: every request carries its protocol version
and the client's capabilities in `_meta`, every result has a `resultType`, list results
carry caching hints, a response answers the id of its request, a message is one line
of JSON. Where the film prints part of a message, what is left out is marked with an
ellipsis.

What is computed:

- the orders table is synthetic (906 rows, a fixed seed), and the function that reads
  it, `late_orders(week)`, is real Python: its source is what the film shows, and its
  result (29 late orders of 412 in week 46) is computed when the module is imported;
- the tool definition is derived from that function's signature and docstring;
- the resource text and the prompt text are what two other small functions return.

`python wire.py` prints every message and the facts the narration states.

The revision matters: 2026-07-28 made the protocol stateless. Earlier revisions opened
with an `initialize` handshake and kept a session (`Mcp-Session-Id`); scene 5 shows both
names struck through. If you learned MCP before that revision, this is the part that
changed.

## What the film leaves out

`server/discover`, elicitation and multi round-trip requests, subscriptions and
change notifications, structured tool output, pagination, the details of
authorization (OAuth, client registration), tasks, and the deprecated client features
(sampling, roots, logging).

## Scenes

`Intro · Alone · Protocol · Call · Doors · Anywhere · Trust · Recap · Outro`, each
renderable alone; `./render.sh` stitches them. Scenes 1 to 5 open on the picture the
previous one ended on (`enter` / `close` in `mcp_film.py`): the cut between two clips
does not show, and every render prints how many pixels differ at each hand-off.

```bash
./render.sh call --quick --check     # layout pass + edge scan + contact sheet
./render.sh                          # whole film, 480p
./render.sh -q h                     # final 1080p60
```

Pacing knobs: `MCP_WPS` (the narrator's words per second, default 2.6), `MCP_QUICK=1` /
`--quick` (collapse the waits).

## Voice-over

The film is paced by its narration: every beat lasts as long as its line takes to say
at 156 words a minute, and the picture changes on the narrator's words. `VOICEOVER.md`
is the timed script and `voiceover.srt` the same lines as subtitles. To regenerate them
after a change:

```bash
MX_TRACE_DIR=/private/tmp/mcp-media/trace ./render.sh -q h
python ../../tools/voiceover.py . -q h
```

## Sources

- Model Context Protocol specification, revision 2026-07-28
  (modelcontextprotocol.io/specification/2026-07-28): base protocol and `_meta`,
  versioning, stdio and Streamable HTTP transports, tools, resources, prompts, and the
  security principles quoted in scene 6.
- The module `mcp_film.py` is named that way on purpose: a file called `mcp.py` would
  shadow the official `mcp` Python package for anything run from this folder.
