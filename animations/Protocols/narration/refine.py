import json
from pathlib import Path
R=Path(__file__).parent
p=json.loads((R/'plan.json').read_text()); d=json.loads((R/'takes.json').read_text())
changes={
'005':'Even light in glass fibre needs more than fifty milliseconds for that single trip.',
'016':'It is cut into packets, here at most fifteen hundred bytes each. Every packet carries its destination, so routers can forward it independently.',
'017':'Routers pass each packet along, hop by hop, using its destination address to choose the way.',
'019':'And an overwhelmed router simply drops what it cannot hold. Watch the queue overflow as packets arrive.',
'028':'If no program listens on that port, the machine itself answers at once with a reset. There is no listener:',
'034':'Refused: something answered no. Usually the machine itself: nothing listens on that port.',
'035':'Timed out: perhaps a firewall dropping packets, or an address where no machine answers. All the caller knows is that nothing came back.',
'036':'TCP numbers every byte.',
'038':'In this model, each packet gets an acknowledgment: I have everything up to here. That returning number tells the sender how far the receiver got.',
'045':'The phone keeps what follows, but cannot hand it to the app. Those later bytes must wait: there is a hole in the stream.',
'047':'and cuts its window. TCP treats this loss as congestion, and sends less at once.',
'064':'So every request here carries the context it needs, including who is asking. This token identifies the caller, and the server checks it each time.',
'067':'HTTP two goes further: several requests travel at once on the same connection. The third lane combines connection reuse with overlapping requests.',
'068':'There is a problem. Those packets cross networks belonging to strangers: a café\'s Wi-Fi, then several operators along the route.',
'070':'and the token. Copying it is enough to pass for Léa. The server accepts the stolen token and answers.',
'072':'Twenty-four euros forty becomes two forty-four. The phone receives that altered amount and cannot detect the change. Reliable delivery does not prevent tampering.',
'073':'HTTPS adds TLS between TCP and HTTP, protecting that conversation.',
'077':'The eavesdropper saw both public values, but lacks the secrets needed to compute the key.',
'082':'One thing is still missing: a certificate is public. Anyone can copy it.',
'083':'So the server signs the handshake with the matching private key, which never leaves it. The signature proves it holds that key.',
'085':'Here, it tries a certificate of its own making. No trusted authority vouches for it, so the chain breaks.',
'086':'The handshake stops right there, with an error pointing to the identity check: certificate verify failed. The request never goes through.',
'089':'Flip a single bit, and the receiver rejects the whole record. It detects the change.',
'093':'In exchange, outsiders cannot read the contents, tampering is detected, and the server proves its identity. The same conversation now travels inside a protected stream.',
'094':'In production, a load balancer receives the request. Often, that is where the sealed pipe ends and the request passes onward.',
'095':'Behind it, the balancer opens its own connection to an application server, which opens others: to a solver, to a database. Every link has its own endpoints.',
'096':'Each link is a separate TCP connection, kept open and reused whenever possible.',
'097':'Not all speak HTTP: a database has its own language for requests and results.',
'098':'But underneath, it is the same reliable stream of bytes, with separate endpoints for each connection.',
'101':'The solver takes three point four seconds, but the balancer only waits three: five zero four. Its deadline expires before the reply.',
'106':'So keep connections open, and put servers close to their users. Shorter distances reduce the delay on every round trip.'
}
for c,t in zip(p['cues'],d['cues']):
 if c['id'] in changes:c['text']=changes[c['id']]
 elif t['gapSec']<0:c['speed']=round(min(1.08,.95*t['durationSec']/(t['roomSec']-.12)),3)
(R/'plan.json').write_text(json.dumps(p,indent=2))
print('rewrites',len(changes),'pace tweaks',[(c['id'],c['speed']) for c in p['cues'] if 'speed' in c])
