# TCP, HTTP, HTTPS

*What really happens when one machine calls another.*

A narrated explainer (the voice carries the explanation; the screen carries data and
almost no sentences). One request is followed from a phone in Paris to a server in
Singapore, down to the wire and back: what a network carries, how TCP turns lossy
packets into a stream, what HTTP says on that stream, what TLS adds, and what the
whole thing looks like between servers in production.

Runtime: **11:24** (683.8 s, measured on the 1080p60 render, `Protocols_1080p60.mp4`;
39 narration lines, 1,389 words at 138 words a minute).

## Scenes

| # | Scene (class) | Question | What you see |
|---|---|---|---|
| 1 | One request (`Request`) | What happened in a third of a second? | A map, Paris to Singapore: light needs 52.5 ms one way, and the trip is made six times. Then the five lines of the client, and the stack of four layers under them. |
| 2 | Packets (`Packets`) | What does a network carry? | A name becomes an address (DNS). A 230 kB picture is cut into 158 packets; routers pass them on, roads differ, one queue overflows. The phone's copy fills in disorder, with nine holes. |
| 3 | A connection (`Connect`) | How do two programs find each other? | A port; SYN, SYN-ACK, ACK traced in time: the handshake, one round trip. A closed port answers at once (refused); a firewall answers nothing: the retries, 1 s apart, then doubling, up to 75 s. Then both again, side by side: what "refused" and "timed out" each tell you. |
| 4 | A reliable stream (`Stream`) | How do lossy packets become a stream? | Numbered bytes, acknowledgments, slow start (trains of 10, 20, 40, 80 packets, the congestion window on a chart); a packet falls off the wire, a hole, what waits behind it, three duplicate ACKs, one resend, and the window cut. |
| 5 | HTTP (`Http`) | What do the programs say? | The real request and response, byte for byte; a route lights; 200, 404, 401, 500, each with its sentence; stateless, hence the token; three lanes of round trips: a connection per request, keep-alive, HTTP/2. |
| 6 | In the clear (`Tap`) | Who else can read it? | A relay on the path reads the request, reuses the token (the server answers it 200 OK), and rewrites 24.4 into 2.44. |
| 7 | HTTPS (`Sealed`) | How to talk privately, with the right server? | One more layer; two secrets, two public values, one key; a chain of certificates up to a root (a demo authority standing in for one of the roots a system ships with); a signature made with the private key that never leaves the server; an impostor with a copied certificate and no key; the same request as noise, with the server's name (SNI) still readable; one flipped bit, rejected. |
| 8 | Between servers (`Servers`) | And in production? | Phone, load balancer, application, solver, database: a relay of connections. A refused port becomes a 502, a wait that runs out a 504. Round trips times distance. |
| 9 | The stack (`Stack`) | How to hold all of it? | The five lines above the stack: each lights what it stands on (the lookup is a directory, not a layer), every layer replays at once, then each line fails with its real error and shows where to look. |

Motif: the five lines of [`demo/client.py`](demo/client.py) and the stack of four
sheets (IP green, TCP blue, TLS purple, HTTP orange), a small copy of which sits top
right in every scene with the layer at hand lit. The camera never moves: depth comes
from an oblique drawing of flat sheets. There is at most one caption per scene
(five in the whole film) and a one-line note at the bottom edge saying where the
scene's data comes from; everything else on screen is data: bytes, packets,
numbers, error messages.

## Render

```bash
./render.sh --list                  # scene names
./render.sh stream --quick --check  # one scene, fast, with edge scan and contact sheet
./render.sh --stitch -q h           # the whole film, 1080p60
```

If `./render.sh` is not executable in your checkout (this repository does not track
file modes), call it as `bash render.sh ...`. Rendering needs only the shared Manim
environment (`tools/requirements-render.txt`); `manim.cfg` switches off Manim's
version check, so a render touches no network.

### Voice-over

The film is paced for a narrator at 138 words a minute (`NET_WPS=2.3` words per
second; set it to re-pace the film). Render with the traces, then build the script:

```bash
MX_TRACE_DIR=/private/tmp/protocols-media/trace ./render.sh --stitch -q h
python ../../tools/voiceover.py . -q h --title "TCP, HTTP, HTTPS"
```

That writes [`VOICEOVER.md`](VOICEOVER.md) (timecodes, room, words per line) and
[`voiceover.srt`](voiceover.srt) (the same lines as subtitles: load it beside the
video to read along while recording, or to watch the silent film).

Every picture is placed on a word of the narration (`cue("phrase")` in the code). To
check them after a change, `python ../../tools/cuesheet.py . -q h` writes one sheet
per scene to `<media>/cues/`: the frame just after each cue, with its phrase.

## What is real, what is a model, what is invented

Nothing in this film was fetched from the network, and baking it touches no network
either: every experiment runs between two programs on this machine's loopback
interface.

**Recorded** (by [`lab.py`](lab.py), from the programs in [`demo/`](demo)):

- the HTTP request and response, byte for byte (117 bytes up, 71 + 83 bytes down);
  the 404, 401 and 500 answers; three requests on one connection against three
  connections;
- what a relay on the path could do to plain HTTP: read everything, reuse the token
  (a second request got `200 OK`), rewrite `24.4` into `2.44` unnoticed;
- a TLS 1.3 handshake seen from that relay: record sizes and order, the ClientHello
  with the server's name readable in it, the request as ciphertext (139 bytes for
  117: 5 of record header, 1 of type, 16 of authentication tag);
- TLS saying no, in the exact words of this machine's library (OpenSSL 3.6 under
  Python 3.12): one flipped bit (`[SSL] record layer failure`), a self-signed
  impostor, a certificate for another name, an expired certificate;
- the key agreement: X25519 computed by [`x25519.py`](x25519.py) (46 lines of code,
  checked against the RFC 7748 vectors) and by OpenSSL, on the same keys, with the same
  result;
- the kernel (macOS): a first congestion window of exactly ten segments; a refused
  connection (`[Errno 61] Connection refused`, well under a millisecond); and
  silence: a connection attempt to `127.0.0.2`, a loopback address where nothing
  answers (the stand-in for a firewall that drops packets), gave up with `[Errno 60]
  Operation timed out` after 75 s. The 75 s were timed; the instants of the SYNs
  (0, 1, 2, 3, 4, 5, 7, 11, 19, 35 and 67 s) are rebuilt from the retransmission
  timer the socket reported while it waited (seeing the SYNs themselves needs a
  packet capture, hence administrator rights);
- the error of an unknown name, `[Errno 8] nodename nor servname provided, or not
  known`: it is what `getaddrinfo` raises here for a name it cannot resolve. It was
  produced with `AI_NUMERICHOST`, which forbids the lookup: no DNS query was sent;
- a small reverse proxy ([`demo/proxy.py`](demo/proxy.py), 53 lines of code)
  answering `502 Bad Gateway` when its upstream's port is closed and `504 Gateway Timeout` after
  waiting 3.0 s for an upstream that needed 3.4 s;
- the number of certificate authorities (195) in the bundle that this laptop's
  OpenSSL reads by default (the one Python uses here). It is not the count of
  macOS's own root store, which is kept elsewhere and differs; the narration says
  "a couple of hundred", which holds for both.

The error numbers and the timers are those of macOS. The causes are the same
everywhere; the wording is not:

| | this Mac (recorded) | Linux (from its documentation, not run here) |
|---|---|---|
| nothing listens | `[Errno 61] Connection refused` | `[Errno 111] Connection refused` |
| nothing answers | `[Errno 60] Operation timed out` after 75 s | `[Errno 110] Connection timed out` after about two minutes |
| SYN sent at | 0, 1, 2, 3, 4, 5, 7, 11, 19, 35, 67 s | up to Linux 6.4: 0, 1, 3, 7, 15, 31, 63 s, about 127 s in all (`tcp_syn_retries` = 6); from Linux 6.5: 0, 1, 2, 3, 4, 5, 7, 11, 19, 35, 67 s, about 131 s (`tcp_syn_linear_timeouts` = 4 adds four one-second retries) |
| unknown name | `[Errno 8] nodename nor servname provided, or not known` | `[Errno -2] Name or service not known` |

Applications usually set a shorter timeout of their own (a few seconds) rather
than wait for the kernel's. Two more things depend on the product, not on the
protocol: a balancer whose upstream refuses the connection answers 502 if it is
nginx, a cloud load balancer or this demo's proxy, and 503 if it is HAProxy or
Envoy (the narration says so); and "refused" can come from something that answers
in the machine's place (a firewall rule that rejects instead of dropping, a
Kubernetes Service with no ready pod).

**A model** (seeing TCP headers needs a packet capture, which needs administrator
rights; loss on a real link cannot be ordered up):

- [`tcpsim.py`](tcpsim.py): the handshake, numbered segments of 1,460 bytes,
  cumulative ACKs, slow start from ten segments, fast retransmit after three
  duplicate ACKs, the window cut (RFC 9293, 5681, 6928). No delayed ACKs, no SACK, no
  retransmission timer. The bytes it carries are the real response (the picture).
  One segment (number 92) is dropped on purpose. The chart and the number beside it
  show the window the sender falls back to after the loss (half of what was in
  flight), not the bookkeeping value that RFC 5681 inflates by one segment per
  duplicate ACK during the recovery: plotted raw, that value climbs while the
  narrator says the server slows down;
- the "best effort" network of scene 2: twelve routers, per-packet routes, one slow
  router with room for five waiting packets. Nine of 158 packets are dropped: a
  demonstration, exaggerated to be visible (the scene says so on screen), not a
  typical loss rate;
- delays: Paris to Singapore along the great circle (10,729 km) at the speed of light
  in optical fibre (group index 1.468, about 204 km per millisecond): 52.5 ms one
  way, 105 ms for a round trip. A lower bound, not a measurement: real cables are
  longer than the great circle and routers add delay. The ledger (three round trips
  for a new HTTPS connection, one on a connection kept open) counts round trips of
  that length;
- HTTP/2 is shown as a drawing (the demo server speaks HTTP/1.1 only).

**Invented**: the delivery service, its name (`api.dispatch.example`), the token
(`lea-4f1c9a`, valid nowhere), the addresses (documentation ranges of RFC 5737), the
certificate authority ("Demo Trust Services", made by [`demo/pki.py`](demo/pki.py)).
Lea's course and its 24.40 euros are the optimum proved in the MIP film; the map is
drawn from that film's assets (map data © OpenStreetMap contributors). In the demo
the client trusts only the demo's own root; the 195 dots are the certificates of
the bundle described above, shown to give the size of a real trust store: on
screen the demo's root is found among them, as a public root would be, and the
scene's note says a demo authority stands in for a public one. The demo listens on
high ports (binding port 443 on the loopback address needs administrator rights);
the film says 443, the convention.

## What the film leaves out

UDP, and QUIC / HTTP/3 on top of it (which merge the TCP and TLS handshakes into one
round trip and drop TCP's single ordered stream); IPv6 and address translation; how
DNS itself works (resolvers, caching, records); TLS session resumption, client
certificates and revocation; HTTP caching, redirects, cookies, WebSockets, gRPC;
flow control (the receiver's window) and the retransmission timer; how routes are
chosen. Four simplifications to know about:

- the film shows per-packet routes and a 6 % loss rate to make "best effort"
  visible: real networks keep the packets of one connection on one route, and lose
  far fewer;
- "HTTP is plain text" is true of HTTP/1.x, the form you read in logs and send with
  `curl`; HTTP/2 and HTTP/3 carry the same methods, paths, headers and status codes
  in a binary framing. Browsers also get concurrency out of HTTP/1.1 by opening
  several connections in parallel: the third lane of scene 5 compares HTTP/2 with
  one kept connection, not with that;
- the stack is drawn with four sheets. The name lookup (DNS) is a service of its
  own that the first line calls, not a fifth layer: it has no sheet;
- the round trips are those of TLS 1.3, which the demo negotiates: one for the TLS
  handshake, so three before the first answer on a new connection. TLS 1.2, still
  met in the field, needs two for its handshake.

## Run it again

```bash
python demo/server.py --tls      # one terminal: HTTPS on 127.0.0.1:8443
python demo/client.py            # another: the five lines, and the reply
python lab.py                    # every experiment, printed
python generate_assets.py        # the whole bake (about 80 s: it waits for a real timeout)
```

The laboratory was run on macOS. One experiment depends on it: the "silence" of
scene 3 connects to `127.0.0.2`, which answers nothing on a Mac; on Linux the whole
`127.0.0.0/8` block is local and the same call is refused at once.

`demo/pki.py` creates the throwaway certificate authority with the `openssl` command
line (3.4 or later) in `~/.cache/manimx/protocols-pki` (or `$PROTOCOLS_PKI`): private
keys never go into the repository. [`assets/curl_verbose.txt`](assets/curl_verbose.txt)
is what `curl -v` printed for the same request: every block of it is one scene of the
film (connected, TLS handshake, certificate, `CERT verify`: the signature of scene 7,
`>` request, `<` response).

The five lines the film shows are the ones `demo/client.py` runs. The fifth,
`reply = read_reply(tls)`, reads one whole response (the head up to the empty line,
then as many bytes as `Content-Length` announces): a single `recv` would return
whatever has arrived so far, since TCP delivers a stream of bytes, not messages.

A re-bake changes what is random or timed (key shares, ciphertext, timings in
`story.json`); the scenes assert the facts they state, and say so if a new machine
answers differently (another trust store, another kernel).

## Files

| File | Role |
|---|---|
| `protocols.py` | the scenes and the narration |
| `kit.py` | the pictures: clock-driven painters (packets, pictures, pipes, ladders), cards, keys, certificates, the stack |
| `lab.py` | the experiments on loopback |
| `tcpsim.py` | the TCP and best-effort models |
| `x25519.py` | the key agreement, in plain Python |
| `generate_assets.py` | bakes `assets/` |
| `demo/` | `server.py`, `client.py`, `proxy.py`, `pki.py`: runnable on their own |
| `manim.cfg` | switches off Manim's version check (no network at render time) |
| `VOICEOVER.md`, `voiceover.srt` | the narration with its timecodes, and the same as subtitles |

## Sources

- RFC 791 (IP), RFC 9293 (TCP), RFC 5681 (congestion control), RFC 6928 (initial
  window of ten segments), RFC 6298 (retransmission timer)
- RFC 9110 and RFC 9112 (HTTP semantics and HTTP/1.1), RFC 9113 (HTTP/2)
- RFC 8446 (TLS 1.3), RFC 7748 (X25519), RFC 5280 (certificates), RFC 6066 (server
  name indication)
- RFC 5737 (documentation addresses), RFC 2606 (`.example`)
- Land outlines: Natural Earth (public domain), from the GeoDetect film's assets
