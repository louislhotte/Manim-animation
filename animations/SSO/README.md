# How SSO Actually Works

A ~4-minute, no-voiceover Manim explainer that takes the "magic" out of Single
Sign-On and shows the real machinery: the redirect dance, the cryptographically
signed token, and the one trust relationship that ties every app to a single
Identity Provider.

It builds the idea from the ground up and stays technically honest — the flow it
animates is the shape of both **SAML 2.0** and **OpenID Connect**, the two
protocols that actually run the internet's SSO.

## What it teaches

- **Why passwords don't scale** — one password per app is one place per app for
  it to leak; reuse turns a single breach into a master key.
- **The three players** — You (the browser), the **App** (a *Service Provider*),
  and the **Identity Provider** (Okta, Google, Azure AD). Apps are set up once to
  *trust* the IdP by holding its public key.
- **The redirect dance** — the six-step SP-initiated flow: open app → redirect to
  IdP → sign in once → signed token → verify signature → session. Your password
  only ever touches the IdP; the app only ever sees a token.
- **The token** — a JWT's `header.payload.signature`; the payload is readable
  claims (`iss`, `sub`, `aud`, `exp`); the IdP **signs** the hash with its private
  key and any app **verifies** it with the public key. Tamper with one character
  and the signature no longer matches — **you can read it, but you can't forge it**.
- **Single Sign-On, in action** — with a live IdP session (a browser cookie),
  every *other* app opens with no new prompt. One logout relocks them all.
- **In the wild** — SAML (XML assertions) vs OIDC (signed JWT on OAuth 2.0), real
  IdPs, and the honest trade-off: one hardened login and central revocation, but
  the IdP becomes the keys to the kingdom (so: phishing-resistant MFA).

Everything on screen is a hand-drawn Manim mobject — the shield IdP, the app
windows, the padlocks, the keys, the signed-token card and the JWT strip. No
assets, no LaTeX (all text is Pango `Text`).

## Scenes

1. **Problem** — a password for every app, and the breach cascade
2. **Players** — User · App (SP) · Identity Provider, and the trust link
3. **Dance** — the redirect flow as a sequence diagram (password only at the IdP)
4. **Token** — JWT anatomy, sign / verify, and a live tamper → *rejected*
5. **Magic** — one IdP session → every door opens instantly; single logout
6. **World** — SAML vs OIDC, real IdPs, and the trade-off

Bookended by the house intro card ("How SSO Actually Works") and the
"Thank you for watching!" / *Created by Ptolémé* outro, with a one-line recap.

## Render

```bash
./render.sh dance --quick -q l   # fast layout check of one scene (480p15)
./render.sh                      # the whole film, 480p
./render.sh full -q h            # final 1080p60 render
./render.sh --stitch -q m        # render each scene and ffmpeg-concat (720p)
```

Scenes: `intro problem players dance token magic world recap outro` (or `full`).

`render.sh` reuses an existing Manim venv in the repo (HarnessEngineering /
Fourier / CNN) if present, otherwise bootstraps a local `.venv` from
`requirements.txt` (`manim` + `numpy`).

### Pacing knobs

The film is deliberately paced for reading. Two independent knobs:

- `SSO_READ` — absolute hold (seconds) after each subtitle lands (default `2.8`).
- `SSO_DELAY` — multiplier for the small pauses between animation steps.
- `SSO_QUICK=1` — collapse every hold for a fast sanity render.

```bash
SSO_READ=3.2 ./render.sh full -q h   # even more reading time
```

## Runtime

Measured full-film duration (1080p60, default pacing): **4:40**
(`media/videos/sso/1080p60/HowSSOWorks.mp4`, 1920×1080 @ 60 fps).
</content>
