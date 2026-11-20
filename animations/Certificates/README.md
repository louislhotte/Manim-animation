# Certificates

How a server proves who it is. A short, narrated, house-style Manim film built on
`manimx`: the voice explains, the screen shows the objects (a key, a name, a card with
four fields, a seal, a fingerprint as a row of coloured cells) and almost no sentences.

## What it teaches

1. **A key is not a name.** A public key says nothing about who sent it: two servers
   can both claim `shop.example`. A certificate binds a name to a key, and is signed by
   someone the browser already trusts.
2. **A signed statement.** Four fields of a certificate matter here (name, public key,
   validity, issuer). The authority hashes them and signs the fingerprint; anyone with
   the authority's public key can check the seal against the fingerprint. Change one
   letter and every byte of the fingerprint changes; without the authority's private
   key, no new seal can be made.
3. **A chain of trust.** The authority has a certificate too, signed by a root, and the
   root signs itself. The root counts because it is already on the device. The browser
   climbs the chain, one seal at a time.
4. **What the browser checks.** At least three things: chain to a trusted root, dates,
   name; the three ways to fail, with Chrome's error names; why a copied certificate is
   not enough (the server must sign the handshake, fresh random numbers included, with
   its private key); why a site's certificate lives shorter and shorter, so that
   renewal has to be automated.

Visual conventions: a hollow key is public, a solid key is private; a seal has the
colour of whoever signed it. Blue is the browser, orange the shop, purple the issuing
authority, green the root and whatever is trusted, gold the thing to look at, red what
fails.

## What is real, and what is not

Nothing was generated with a certificate tool and no key exists: by choice, nothing was
executed for this film beyond Manim and plain Python. The certificates are an
**illustration**, written by hand in `facts.py` with names from the reserved `.example`
domain, and a note at the bottom of the screen says so.

What is computed (and asserted when `facts.py` is imported):

- the fingerprint is the SHA-256 (`hashlib`) of the card's four lines, the key being
  the placeholder text "the shop's public key" since no key exists. The "one letter"
  beat really changes `shop.example` into `sh0p.example`, and the count on screen (32
  of 32 bytes differ) is counted, not chosen;
- the three checks of the last scene are evaluated on the fields (dates against the
  day the film was made, the name against the address typed), for the good certificate
  and for the three broken ones;
- the illustrative certificate runs for the longest period allowed on its date of
  issue (200 days, both ends counted).

`python facts.py` prints all of it.

Two simplifications to know about. The picture of the seal being checked (the public
key gives back the fingerprint that was signed, and the two rows are compared) is how
an RSA signature works; with ECDSA nothing is recovered, the verifier checks an
equation over the fingerprint, the signature and the public key. The narration only
says that the seal is checked against the fingerprint, which holds for both. And the
name of a real certificate lives in its "subject alternative name" extension, among
other fields (serial number, algorithm, extensions) that the card leaves out.

## Sources

- Maximum lifetime of a publicly trusted TLS server certificate: CA/Browser Forum
  ballot SC-081v3 (adopted 11 April 2025): 398 days (since 1 September 2020), 200 days
  from 15 March 2026, 100 days from 15 March 2027, 47 days from 15 March 2029. Cited on
  screen. Authorities' own certificates and private ones are not bound by it.
- Error names: as Chrome prints them on its error page (`NET::ERR_CERT_AUTHORITY_INVALID`,
  `NET::ERR_CERT_DATE_INVALID`, `NET::ERR_CERT_COMMON_NAME_INVALID`). Other browsers
  use other names; the screen says whose they are.
- "128 roots": the number of certificates in `/etc/ssl/cert.pem` on the Mac that
  rendered the film (counted on 2026-11-20). That file is the macOS bundle for
  command-line tools; Safari, Chrome and Firefox each use their own list, with other
  counts. The screen says which list it is, and the narration only says "more than a
  hundred".
- In TLS 1.3 the proof that the server holds the private key is the `CertificateVerify`
  message: a signature over the handshake so far, which includes the client's fresh
  random numbers. The eight cells of the last scene stand for those.

## What the film leaves out

Revocation (CRL, OCSP), Certificate Transparency, wildcard and multi-name certificates,
extended validation, cross-signing, client certificates, and how the key exchange of
TLS itself works (see `animations/Protocols`, scene 7).

## Scenes

`Intro · Claim · Seal · Chain · Checks · Outro`, each renderable alone; `./render.sh`
stitches them.

**Measured runtime:** 3:01 (181.5 s at 1080p60), 15 narration lines, 387 words.
`Certificates_1080p60.mp4` in this folder is the final render (videos are git-ignored).

Checked before release: `--check` and the lint on every scene; `tools/motioncheck.py`
(51 to 79 % of each scene moving; two near-still stretches of 2 s or more in the whole
film, 2.0 s and 2.8 s);
`tools/cuesheet.py` (one frame per narrated cue); full-size 1080p frames; and an
independent read of every narration line and on-screen claim, whose findings were
applied.

```bash
./render.sh seal --quick --check     # layout pass + edge scan + contact sheet
./render.sh                          # whole film, 480p
./render.sh -q h                     # final 1080p60
```

Pacing knobs: `CERT_WPS` (the narrator's words per second, default 2.6), `CERT_QUICK=1`
/ `--quick` (collapse the waits).

## Voice-over

The film is paced by its narration: every beat lasts as long as its line takes to say
at 156 words a minute, and the picture changes on the narrator's words. `VOICEOVER.md`
is the timed script and `voiceover.srt` the same lines as subtitles. To regenerate them
after a change:

```bash
MX_TRACE_DIR=/private/tmp/certificates-media/trace ./render.sh -q h
python ../../tools/voiceover.py . -q h
```
