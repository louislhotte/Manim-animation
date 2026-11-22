# Voice-over script: MCP, the Model Context Protocol

Film length **4:47** (287.3 s), 26 lines, 636 words. Timecodes are from the 1080p60 render; every line starts when its caption appears.

*Room* is the time until the next line starts. The pacing assumes 156 words a minute, so a line of *n* words wants about n / 2.6 seconds. A line marked **TIGHT** has less than that.

`voiceover.srt` holds the same lines as subtitles: load it next to the video to read along while recording.

## Intro  (0:00 to 0:13)

**0:00.0**  room 14.0 s, 28 words (about 10.8 s)

> MCP, the Model Context Protocol. How does an AI application reach the tools and data it needs? Follow one question, from a model to a database and back.

## Alone  (0:13 to 0:39)

**0:14.0**  room 7.2 s, 17 words (about 6.5 s)

> A language model does one thing. It reads the text in its context, and writes more text.

**0:21.2**  room 9.6 s, 23 words (about 8.8 s)

> Ask it how many orders shipped late in week forty-six, and it cannot know. The answer sits in a database it cannot reach.

**0:30.8**  room 8.9 s, 18 words (about 6.9 s)

> The Model Context Protocol, MCP, is a standard way to bring that outside world into the model's context.

## Protocol  (0:39 to 1:32)

**0:39.6**  room 16.5 s, 41 words (about 15.8 s)

> It names three roles. The application you talk to, a chat window or a code editor, is the host. Each outside system is wrapped by a small program, a server. And inside the host, one client per server speaks the protocol.

**0:56.1**  room 9.2 s, 22 words (about 8.5 s)

> They exchange plain JSON messages. A request names a method and carries an id. The response comes back with the same id.

**1:05.3**  room 14.2 s, 35 words (about 13.5 s)

> This first request asks: which tools do you have? The server answers with its list. Each tool is a name, a description, and a schema for its arguments, often built straight from a function's signature.

**1:19.5**  room 13.1 s, 29 words (about 11.2 s)

> The host places those definitions in the model's context. That is the context in the name: the protocol exists to put the right text in front of the model.

## Call  (1:32 to 2:21)

**1:32.6**  room 9.9 s, 24 words (about 9.2 s)

> Now the same question. The model reads it, sees a tool that fits, and writes a call: a name and arguments. Still only text.

**1:42.5**  room 9.0 s, 20 words (about 7.7 s)

> The host catches it, and first asks you. The specification wants a human in the loop, able to say no.

**1:51.5**  room 10.3 s, 25 words (about 9.6 s)

> Then the client sends the call. The server runs its function against the table: four hundred and twelve orders that week, twenty-nine of them late.

**2:01.8**  room 6.9 s, 16 words (about 6.2 s)

> The result travels back under the same id, and lands in the context as more text.

**2:08.7**  room 13.2 s, 30 words (about 11.5 s)

> The model reads again, and answers. It never touched the database, and never saw its password. It wrote a request, the host carried it, and the server did the work.

## Doors  (2:21 to 2:55)

**2:21.9**  room 8.0 s, 19 words (about 7.3 s)

> Tools are one of three things a server can offer. What separates them is who decides to use them.

**2:29.9**  room 6.5 s, 14 words (about 5.4 s)

> A prompt is a ready-made message. The user picks it, like a slash command.

**2:36.4**  room 7.2 s, 17 words (about 6.5 s)

> A resource is data with an address: here, the table's schema. The application decides to attach it.

**2:43.6**  room 4.9 s, 11 words (about 4.2 s)

> And a tool, as we saw, runs when the model decides.

**2:48.5**  room 7.0 s, 14 words (about 5.4 s)

> Three doors, and all of them lead to the same place: the model's context.

## Anywhere  (2:55 to 3:39)

**2:55.6**  room 11.5 s, 28 words (about 10.8 s)

> Where does a server run? On your own machine, the host starts it as a child process, and they exchange lines of JSON over standard input and output.

**3:07.0**  room 8.0 s, 19 words (about 7.3 s)

> Or far away. Then every request is an HTTP POST, and an access token can say who is asking.

**3:15.1**  room 9.9 s, 24 words (about 9.2 s)

> Since the July twenty twenty-six revision, there is no handshake and no session. Every request carries the protocol version and what the client supports.

**3:25.0**  room 14.6 s, 30 words (about 11.5 s)

> So a busy server can run as many copies as it needs behind a load balancer. Any copy can answer any request, and if one disappears, the others carry on.

## Trust  (3:39 to 4:24)

**3:39.6**  room 11.9 s, 29 words (about 11.2 s)

> That is the payoff. Wrap a system once, and every host that speaks the protocol can use it. Three hosts and four systems: seven pieces to build, not twelve.

**3:51.5**  room 11.5 s, 28 words (about 10.8 s)

> But look at what you are plugging in. A server's tools are code that can run with your access. And its descriptions are text your model will read.

**4:03.0**  room 21.5 s, 51 words (about 19.6 s)

> A dishonest server can hide an instruction there, and the model may follow it, using a tool from a server you trust. So the specification says: treat a description as untrusted, unless you trust the server it came from. Keep a human in the loop, and connect only servers you trust.

## Recap  (4:24 to 4:35)

**4:24.5**  room 11.1 s, 24 words (about 9.2 s)

> A model that only reads and writes text. A host that carries its requests. Servers that do the work. And one protocol between them.

## Outro  (4:35 to 4:47)

**4:35.6**  no narration (11.7 s).
