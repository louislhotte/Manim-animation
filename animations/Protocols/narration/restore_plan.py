import json
from pathlib import Path
R=Path(__file__).parent
raw='''0.00|TCP, HTTP, HTTPS. What really happens when one machine calls another? Follow one request from a phone in Paris to a server in Singapore, down through the layers that make it work.
14.48|Léa is a courier working in Paris. She taps her screen, and a third of a second later, at best, her next deliveries appear.
23.61|That answer has travelled all the way from a server in Singapore.
27.77|Ten thousand seven hundred kilometres away.
30.38|Even light, travelling through glass fibre, needs more than fifty milliseconds for that single trip.
36.03|And before the answer arrived, the trip was made six times: three complete round trips, back and forth across that distance.
44.12|Why three? Because her app does not simply send one message.
48.46|It runs five small steps: find the server's address, open a connection,
53.68|secure it, send a request, and finally read the reply.
58.27|Each step speaks a protocol, and each protocol relies on the one below it.
63.92|So start at the bottom. What does a network really carry? Follow the data, and those four layers will start to make sense.
72.32|First, the address. A directory service, DNS, turns the server's name into a number: an IP address.
79.71|The phone and the server use these addresses to exchange packets.
84.27|Now the server sends Léa the map of her course: two hundred and thirty kilobytes of image data.
90.79|This network cannot carry it in one piece.
93.83|It is cut into packets, here at most fifteen hundred bytes each. Every packet carries its destination, so it can be forwarded independently.
101.90|Routers pass each packet along, hop by hop, using its destination address to choose the next hop.
107.55|Packets may take different roads, and even overtake each other.
111.47|And a router that is overwhelmed simply drops what it cannot hold. Watch the queue overflow as packets keep arriving.
118.08|This is all the Internet Protocol promises: its best effort.
122.43|In this run, nine packets of the picture never arrived. The red gaps show exactly what is missing. The network itself does not repair them.
131.33|TCP repairs all this, and it starts with a connection.
135.68|On the server, a program listens on a numbered door, called a port. Four four three is the usual port for HTTPS.
145.05|The phone sends a packet flagged SYN: let's synchronise.
148.96|The server answers SYN, ACK. The phone acknowledges.
152.44|This is the handshake: three packets, one round trip,
156.35|and each side knows the other is there. The connection is ready, but no application data has moved yet.
163.12|If no program listens on that port, the machine itself answers at once with a reset:
170.07|connection refused. An answer comes back immediately.
173.78|But if a firewall silently drops the packet, nothing comes back.
178.57|The phone asks again after one second, and again,
182.48|then waits longer and longer, before giving up. Here, that happens after seventy-five seconds.
188.78|A refusal is fast, a timeout is slow, and that difference already tells us where to look for the failure.
195.74|Refused: something answered no. Usually the machine itself, because nothing listens on that port.
201.39|Timed out: perhaps a firewall dropping packets, or an address where no machine answers. The caller only knows that no reply came back.
209.85|Once connected, TCP numbers every byte.
212.46|Each packet says where its bytes belong, so the phone can put them back in order, even after a scrambled arrival.
219.41|In this model, each packet gets an acknowledgment: I have everything up to here. That returning number tells the sender how far the receiver has got.
227.92|The server starts carefully: ten packets.
230.53|Each acknowledgment that comes back lets it send two more.
234.87|Twenty packets in the second round trip: this is slow start.
239.66|Forty in the third: the window doubles each round.
244.00|And in the fourth, eighty packets.
247.28|Then a packet is lost.
249.46|The phone keeps what follows, but cannot hand it to the app: there is a hole in the stream.
256.41|Its acknowledgments repeat the same number. Three repeats, and the server sends that missing packet again,
262.94|and cuts its window. TCP treats this loss as congestion, reducing how much it sends at once.
268.70|One more round trip, and
270.87|the hole is filled. The picture is complete: every byte, in order.
276.09|That is TCP's promise: bytes go in at one end, and the same bytes come out at the other, in order. The application works with a stream, while TCP handles the missing pieces underneath.
288.37|On that stream, the two programs can finally talk.
292.28|Their language is HTTP. Version one uses plain text.
296.63|A request: a method, GET; a path, which says what is wanted;
301.84|then headers, one per line. Finally, an empty line marks the end of the headers. This GET request needs no body.
309.03|The server reads the path, finds the function in charge,
313.38|and answers in the same style: a status line, headers, an empty line, and the body.
320.34|Here, Léa's delivery course, as JSON.
323.62|The status code says how it went. Two hundred: fine.
327.96|Four hundred and four: the caller asked for something that does not exist.
333.62|Four hundred and one: the request lacks valid credentials to identify the caller.
338.83|Five hundred: the server itself failed.
341.44|So read the first digit. Four means a client error. Five means a server error. That is the first clue.
347.77|HTTP is stateless: nothing in the protocol ties a request to the one before it.
353.85|So every request here carries the context it needs, including who is asking. That is what this token is for: the server checks it with each request.
362.35|Opening a connection for every request costs two round trips each time.
367.57|Keep the connection, and the next request costs one: that is keep-alive.
372.78|HTTP two goes further: several requests travel at once on the same connection. The three lanes show how connection reuse and overlapping requests avoid repeated waiting.
382.40|There is a problem. Those packets cross networks that belong to strangers: a café's Wi-Fi, then several operators along the route.
390.22|Anyone on the path can read every byte: the path, the answer,
395.44|and the token. Here, copying that token is all it takes to pass for Léa and get an accepted response.
401.77|They can also change bytes on the way.
405.24|Twenty-four euros forty becomes two forty-four. The phone receives the altered amount and has no way to detect the change. Reliable delivery alone offers no protection.
414.13|HTTPS closes both holes by slipping one more protocol, TLS, between TCP and HTTP.
420.22|It begins with a handshake of its own.
423.70|Each side invents a secret number, and sends the other a public value computed from it. The secret stays on its own machine.
432.10|Mixing its own secret with the other's public value, each side arrives at the same key. Both results match.
439.05|The eavesdropper saw both public values, but without either secret, cannot compute that shared key.
444.51|But a key shared with whom? The server must also prove its name.
449.73|It presents a certificate, signed by an authority,
453.21|itself signed by a root that the phone already trusts. That root comes from the trusted authorities installed on the system, shown here as the grid below.
462.34|The chain holds, and the name matches the server being contacted.
466.50|One thing is still missing: a certificate is public. Anyone can copy it and present that same document.
472.15|So the server signs the handshake with the matching private key, which never leaves it. This proves it actually holds the key for that certificate.
479.78|An impostor can copy the certificate, but not that private key.
484.13|Here, it tries a certificate of its own making, which no trusted authority vouches for. The trust chain breaks.
490.65|The handshake stops right there, with an error that points to the identity check: certificate verify failed. The connection is rejected before the request goes through.
498.71|From then on, every application byte is sealed.
501.76|On the wire, the same request becomes unreadable noise.
505.24|Flip a single bit, and the receiver rejects the whole record. Tampering is detected.
510.02|What still shows: the two addresses, the size of the messages,
514.80|and, in this handshake, the server's name, in a field called SNI.
520.23|The price, with TLS one point three: one more round trip when the connection opens.
526.75|In exchange, outsiders cannot read the contents, tampering is detected, and the server proves its identity. The HTTP conversation stays the same, inside a protected stream.
536.45|In production, a load balancer receives the request, and that is often where the sealed pipe ends. It handles the incoming secure connection.
543.84|Behind it, the balancer opens its own connection to an application server, which opens others: to a solver, to a database. One incoming request can therefore start several separate conversations.
554.56|Each link is a separate TCP connection, kept open and reused whenever possible, as the pulses show.
560.22|Not all of them speak HTTP. A database has its own language for requests and results.
565.43|But underneath, it is the same reliable stream of bytes. Each connection has its own endpoints.
570.90|So when something breaks, the chain tells us where.
574.81|The application is down: its port refuses, and the balancer answers five zero two, or five zero three with some products.
583.94|The solver takes three point four seconds, but the balancer only waits three: five zero four. The upstream reply arrives too late for that deadline.
592.51|And every hop costs time.
594.69|A round trip to Singapore: a hundred and five milliseconds, at best.
599.91|A new secure connection needs three of them before the answer comes;
605.12|an open one, just one.
607.30|So keep connections open, and put servers close to their users. The shorter distance reduces the delay on every round trip.
614.88|Back to the five lines.
617.06|The first asks a directory for an address.
620.53|The second opens a connection: TCP, a reliable stream of bytes, on top of IP, packets with no guarantee.
628.79|The third seals it: TLS, a private stream with a proven identity.
634.01|The last two speak HTTP: send a request, and read a response.
639.46|And each line fails in its own way.
642.94|The first: the name is unknown.
645.55|The second: a refusal, if nothing listens; a timeout, if nothing answers.
650.77|The third: a certificate that does not check out.
654.68|The last two: a status code.
657.29|Find the line that failed, and the error points to the layer that needs attention. Start investigating there.
663.38|One request, four layers: each one simpler because of the one below it. Together, they turn unreliable packets into a meaningful, protected conversation.
672.80|Packets carry bytes. TCP puts them in order. TLS protects the stream.
678.15|And HTTP gives the conversation meaning. Four layers working together. Thank you for watching.'''
rows=[]
for i,line in enumerate(raw.splitlines()):
 t,text=line.split('|',1); rows.append({'id':f'{i+1:03}','startSec':float(t),'text':text})
for i,r in enumerate(rows):r['latestEndSec']=(rows[i+1]['startSec']-.08) if i+1<len(rows) else 683.30
p={'sourceVideo':str(R.parent/'Protocols_1080p60.mp4'),'durationSec':683.814714,'cues':rows}
(R/'plan.json').write_text(json.dumps(p,indent=2))
print(len(rows),sum(len(r['text'].split()) for r in rows))
