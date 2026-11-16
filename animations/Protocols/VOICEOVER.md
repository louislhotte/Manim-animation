# Voice-over script: TCP, HTTP, HTTPS

Film length **11:23** (683.8 s), 39 lines, 1389 words. Timecodes are from the 1080p60 render; every line starts when its caption appears.

*Room* is the time until the next line starts. The pacing assumes 138 words a minute, so a line of *n* words wants about n / 2.3 seconds. A line marked **TIGHT** has less than that.

`voiceover.srt` holds the same lines as subtitles: load it next to the video to read along while recording.

## Intro  (0:00 to 0:13)

**0:00.0**  room 14.0 s, 27 words (about 11.7 s)

> TCP, HTTP, HTTPS: what really happens when one machine calls another. We will follow a single request, from a phone in Paris to a server in Singapore.

## Request  (0:13 to 1:11)

**0:14.5**  room 13.3 s, 28 words (about 12.2 s)

> Léa, a courier in Paris, taps her screen. A third of a second later, at best, her next deliveries are there. They came from a server in Singapore.

**0:27.8**  room 16.3 s, 33 words (about 14.3 s)

> Ten thousand seven hundred kilometres away. Even light, in glass fibre, needs more than fifty milliseconds for that trip. And before the answer arrived, the trip was made six times: three round trips.

**0:44.1**  room 14.1 s, 30 words (about 13.0 s)

> Why three? Because her app does not send one message. It runs five small steps: find the server's address, open a connection, secure it, send a request, read the reply.

**0:58.3**  room 13.5 s, 24 words (about 10.4 s)

> Each step speaks a protocol, and each protocol relies on the one below. So start at the bottom: what does a network really carry?

## Packets  (1:11 to 2:10)

**1:12.3**  room 12.0 s, 24 words (about 10.4 s)

> First, the address. A directory service, DNS, turns the server's name into a number: an IP address. Every machine on the Internet has one.

**1:24.3**  room 17.6 s, 38 words (about 16.5 s)

> Now the server sends Léa the map of her course: two hundred and thirty kilobytes. No network carries that in one piece. It is cut into packets of at most fifteen hundred bytes, each stamped with its destination.

**1:41.9**  room 16.2 s, 34 words (about 14.8 s)

> Routers pass each packet along, hop by hop, looking only at that address. Packets may take different roads, and overtake each other. And a router that is overwhelmed simply drops what it cannot hold.

**1:58.1**  room 12.7 s, 24 words (about 10.4 s)
*On screen: The network promises nothing: only its best effort.*

> This is all the Internet Protocol promises: its best effort. In this run, nine packets of the picture never arrived, and nobody was told.

## Connect  (2:10 to 3:29)

**2:11.3**  room 13.7 s, 29 words (about 12.6 s)

> TCP repairs all this, and it starts with a connection. On the server, a program listens on a numbered door, a port: four four three, by convention, for HTTPS.

**2:25.0**  room 18.1 s, 39 words (about 17.0 s)

> The phone sends a packet flagged SYN: let's synchronise. The server answers SYN, ACK. The phone acknowledges. This is the handshake: three packets, one round trip, and each side knows the other is there. No data has moved yet.

**2:43.1**  room 10.7 s, 22 words (about 9.6 s)

> If no program listens on that port, the machine itself answers at once with a reset: connection refused. The failure is instant.

**2:53.8**  room 15.0 s, 32 words (about 13.9 s)

> But if a firewall silently drops the packet, nothing comes back. The phone asks again after one second, and again, then waits longer and longer, and gives up: here, after seventy-five seconds.

**3:08.8**  room 20.6 s, 42 words (about 18.3 s)

> A refusal is fast, a timeout is slow, and that alone tells you where to look. Refused: something answered no. Usually the machine itself: nothing listens on that port. Timed out: a firewall, most often; or an address where no machine answers.

## Stream  (3:29 to 4:47)

**3:29.8**  room 18.1 s, 39 words (about 17.0 s)

> Once connected, TCP numbers every byte. Each packet says where its bytes belong, so the phone can put them back in order. And for each packet it receives, it answers with an acknowledgment: I have everything up to here.

**3:47.9**  room 19.4 s, 42 words (about 18.3 s)

> The server starts carefully: ten packets. Each acknowledgment that comes back lets it send two more. Twenty packets in the second round trip: this is slow start. Forty in the third: its congestion window doubles every time. And in the fourth, eighty.

**4:07.3**  room 21.4 s, 46 words (about 20.0 s)

> Then a packet is lost. The phone keeps what follows, but cannot hand it to the app: there is a hole. Its acknowledgments repeat the same number. Three repeats, and the server sends that packet again, and cuts its window: to TCP, a loss means congestion.

**4:28.7**  room 19.2 s, 36 words (about 15.7 s)
*On screen: TCP: bytes go in at one end and come out at the other, in order.*

> One more round trip, and the hole is filled: the picture is complete, every byte, in order. That is TCP's promise: bytes go in at one end, and the same bytes come out at the other.

## Http  (4:47 to 6:21)

**4:48.4**  room 20.7 s, 45 words (about 19.6 s)

> On that stream, the two programs can finally talk. Their language is HTTP: in its classic form, plain text. A request: a method, GET; a path, which says what is wanted; then headers, one per line, and an empty line to say: I am done.

**5:09.0**  room 14.6 s, 31 words (about 13.5 s)

> The server reads the path, finds the function in charge, and answers in the same style: a status line, headers, an empty line, and the body. Here, Léa's course, as JSON.

**5:23.6**  room 24.1 s, 53 words (about 23.0 s)

> The status code says how it went. Two hundred: fine. Four hundred and four: the caller asked for something that does not exist. Four hundred and one: the caller did not say who is asking. Five hundred: the server itself failed. So read the first digit: four, the caller's mistake; five, the server's.

**5:47.8**  room 14.6 s, 31 words (about 13.5 s)

> HTTP is stateless: nothing in the protocol ties a request to the one before. So every request must carry everything, including who is asking. That is what this token is for.

**6:02.3**  room 19.5 s, 37 words (about 16.1 s)

> Opening a connection for every request costs two round trips each time. Keep the connection, and the next request costs one: that is keep-alive. HTTP 2 goes further: several requests travel at once on the same connection.

## Tap  (6:21 to 6:53)

**6:22.4**  room 19.4 s, 42 words (about 18.3 s)

> There is a problem. Those packets cross networks that belong to strangers: a café's Wi-Fi, then several operators. Anyone on the path can read every byte: the path, the answer, and the token, which is all it takes to pass for Léa.

**6:41.8**  room 11.9 s, 22 words (about 9.6 s)

> They can also change bytes on the way. Twenty-four euros forty becomes two forty-four, and the phone has no way to know.

## Sealed  (6:53 to 8:55)

**6:54.1**  room 18.0 s, 38 words (about 16.5 s)

> HTTPS closes both holes by slipping one more protocol, TLS, between TCP and HTTP. It begins with a handshake of its own. Each side invents a secret number, and sends the other a public value computed from it.

**7:12.1**  room 12.4 s, 26 words (about 11.3 s)

> Mixing its own secret with the other's public value, each side arrives at the same key. The eavesdropper saw both public values, and cannot compute it.

**7:24.5**  room 22.0 s, 48 words (about 20.9 s)

> But a key shared with whom? The server must prove its name. It presents a certificate, signed by an authority, itself signed by a root that the phone already trusts: one of the couple of hundred that every system ships with. The chain holds, and the name matches.

**7:46.5**  room 13.3 s, 28 words (about 12.2 s)

> One thing is still missing: a certificate is public, anyone can copy it. So the server signs the handshake with the matching private key, which never leaves it.

**7:59.8**  room 18.9 s, 41 words (about 17.8 s)

> An impostor can copy the certificate, but not that key. Its only option is a certificate of its own making, which no authority vouches for. The handshake stops right there, with an error you will meet one day: certificate verify failed.

**8:18.7**  room 21.5 s, 46 words (about 20.0 s)

> From then on, every byte is sealed. On the wire, the same request is noise. Flip a single bit, and the receiver rejects the whole record. What still shows: the two addresses, the size of the messages, and the server's name, in a field called SNI.

**8:40.2**  room 15.7 s, 29 words (about 12.6 s)
*On screen: HTTPS: the same conversation, in a sealed pipe.*

> The price, with TLS one point three: one more round trip when the connection opens. In exchange: nobody can read, nobody can alter, and you know who is answering.

## Servers  (8:55 to 10:14)

**8:56.4**  room 18.1 s, 38 words (about 16.5 s)

> In production, a load balancer receives the request, and that is usually where the sealed pipe ends. Behind it, the balancer opens its own connection to an application server, which opens others: to a solver, to a database.

**9:14.6**  room 16.3 s, 35 words (about 15.2 s)

> Each link is a separate TCP connection, kept open and reused whenever possible. Not all of them speak HTTP: a database has its own language. But underneath, it is the same reliable stream of bytes.

**9:30.9**  room 21.6 s, 46 words (about 20.0 s)

> So when something breaks, the chain tells you where. The application is down: its port refuses, and the balancer answers five zero two, or five zero three with some products. The solver takes three point four seconds, but the balancer only waits three: five zero four.

**9:52.5**  room 21.9 s, 45 words (about 19.6 s)
*On screen: Latency is round trips, times distance.*

> And every hop costs time. A round trip to Singapore: a hundred and five milliseconds, at best. A new secure connection needs three of them before the answer comes; an open one, just one. So keep connections open, and put servers close to their users.

## Stack  (10:14 to 11:12)

**10:14.9**  room 24.6 s, 54 words (about 23.5 s)

> Back to the five lines. The first asks a directory for an address. The second opens a connection: TCP, a reliable stream of bytes, on top of IP, packets with no guarantee. The third seals it: TLS, a private stream with a proven identity. The last two speak HTTP: a request, and a response.

**10:39.5**  room 23.9 s, 52 words (about 22.6 s)

> And each line fails in its own way. The first: the name is unknown. The second: a refusal, if nothing listens; a timeout, if nothing answers. The third: a certificate that does not check out. The last two: a status code. Find the line that failed, and you know where to look.

**11:03.4**  room 8.8 s, 13 words (about 5.7 s)
*On screen: One request, four layers: each one simple, because of the one below.*

> One request, four layers: each one simple, because of the one below it.

## Outro  (11:12 to 11:23)

**11:12.1**  no narration (11.7 s).
