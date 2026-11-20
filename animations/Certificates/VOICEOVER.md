# Voice-over script: Certificates

Film length **3:01** (181.5 s), 15 lines, 387 words. Timecodes are from the 1080p60 render; every line starts when its caption appears.

*Room* is the time until the next line starts. The pacing assumes 156 words a minute, so a line of *n* words wants about n / 2.6 seconds. A line marked **TIGHT** has less than that.

`voiceover.srt` holds the same lines as subtitles: load it next to the video to read along while recording.

## Intro  (0:00 to 0:13)

**0:00.0**  room 14.0 s, 21 words (about 8.1 s)

> Certificates. How does a server prove who it is? With a name, a key, and a signature that anyone can check.

## Claim  (0:13 to 0:43)

**0:14.0**  room 11.1 s, 27 words (about 10.4 s)

> Your browser connects to shop dot example, and a server answers with its public key. But anyone can make a key, and anyone can claim a name.

**0:25.1**  room 7.3 s, 17 words (about 6.5 s)

> Two servers, two keys, the same claim. Nothing here tells the browser which one is the shop.

**0:32.3**  room 10.8 s, 22 words (about 8.5 s)

> A certificate settles it. It is a statement that this key belongs to this name, signed by someone the browser already trusts.

## Seal  (0:43 to 1:24)

**0:43.1**  room 8.4 s, 20 words (about 7.7 s)

> Inside, four fields matter: the name, the public key, the dates between which it is valid, and who issued it.

**0:51.5**  room 14.9 s, 37 words (about 14.2 s)

> The issuer is a certificate authority. Once it has checked that the shop controls the name, it hashes those fields into a fingerprint, and signs the fingerprint with its own private key. That signature is the seal.

**1:06.4**  room 8.0 s, 19 words (about 7.3 s)

> Anyone holding the authority's public key can check the seal against the fingerprint. They agree: the certificate is intact.

**1:14.4**  room 10.0 s, 21 words (about 8.1 s)

> Change a single letter, and nothing matches any more. And without the authority's private key, nobody can make a new seal.

## Chain  (1:24 to 1:55)

**1:24.4**  room 8.8 s, 21 words (about 8.1 s)

> But who vouches for the authority? Another certificate: its key is signed by a root authority. And the root signs itself.

**1:33.2**  room 11.1 s, 27 words (about 10.4 s)

> That would prove nothing, except for one thing. The root is already on your device: operating systems and browsers ship with more than a hundred of them.

**1:44.3**  room 10.8 s, 23 words (about 8.8 s)

> So the browser climbs. Each seal is checked with the key of the certificate above, until it reaches a root it already holds.

## Checks  (1:55 to 2:49)

**1:55.1**  room 12.3 s, 30 words (about 11.5 s)

> On every connection, the browser checks at least three things. The chain reaches a root it trusts. Today is inside the validity dates. The name matches the address you typed.

**2:07.3**  room 11.5 s, 28 words (about 10.8 s)

> Fail any one of them, and the browser stops you: an issuer it does not know, a date that has passed, or a name that does not match.

**2:18.8**  room 13.8 s, 34 words (about 13.1 s)

> One last thing: a certificate is public, so anyone can copy it. That is why the server must also sign this handshake, fresh random numbers included, with the private key that never leaves it.

**2:32.6**  room 17.3 s, 40 words (about 15.4 s)

> And a site's certificate expires on purpose, sooner and sooner: two hundred days at most in twenty twenty-six, forty-seven from twenty twenty-nine. So renewal has to be automated: a program proves it controls the name, and collects a fresh certificate.

## Outro  (2:49 to 3:01)

**2:49.9**  no narration (11.7 s).
