# Voice-over script: Terraform

Film length **5:58** (358.2 s), 27 lines, 690 words. Timecodes are from the 1080p60 render; every line starts when its caption appears.

*Room* is the time until the next line starts. The pacing assumes 138 words a minute, so a line of *n* words wants about n / 2.3 seconds. A line marked **TIGHT** has less than that.

`voiceover.srt` holds the same lines as subtitles: load it next to the video to read along while recording.

## Intro  (0:00 to 0:13)

**0:00.0**  room 14.0 s, 23 words (about 10.0 s)

> Terraform: how a text file becomes real infrastructure. We will follow one small example, from an empty cloud region to three full environments.

## Apply  (0:13 to 0:52)

**0:14.5**  room 12.9 s, 27 words (about 11.7 s)
*On screen: Five blocks of text describe a small piece of cloud infrastructure.*

> This is a Terraform file. Five short blocks, each describing a piece of cloud infrastructure: a network, a subnet, a firewall, two servers, and a storage bucket.

**0:27.3**  room 13.2 s, 26 words (about 11.3 s)
*On screen: One command builds all of it, in the right order.*

> None of it exists yet. Run one command, terraform apply, say yes, and Terraform calls the cloud's API to build it all, in the right order.

**0:40.5**  room 12.3 s, 23 words (about 10.0 s)
*On screen: Infrastructure as code: the file is the source of truth.*

> From now on, the file is the source of truth. To change the cloud, you change the file. That is infrastructure as code.

## Blocks  (0:52 to 1:40)

**0:53.3**  room 22.0 s, 48 words (about 20.9 s)
*On screen: One block declares a resource: a type, a name, its arguments.*

> Open one block. The keyword resource means: this should exist. Then its type, an AWS server, and a name you choose. Inside, its arguments. Count equals two: this one block declares two servers, web zero and web one. Then their image, their size, their subnet and their firewall.

**1:15.3**  room 12.4 s, 26 words (about 11.3 s)
*On screen: You declare the result. Terraform works out the steps.*

> Notice what is missing: steps. You never write create this, wait for that, then launch. You declare the result, and Terraform works out the API calls.

**1:27.7**  room 12.8 s, 24 words (about 10.4 s)
*On screen: A provider is a plugin that speaks one platform's API.*

> Those calls come from a provider, a plugin that speaks one API. There are providers for AWS, Azure, Google Cloud, Kubernetes, and thousands more.

## Graph  (1:40 to 2:34)

**1:41.0**  room 14.2 s, 30 words (about 13.0 s)
*On screen: A block can use a value from another block.*

> Blocks can point at each other. The subnet needs the network's ID, which does not exist yet, so it references it. Terraform now knows the subnet depends on the network.

**1:55.1**  room 11.1 s, 23 words (about 10.0 s)
*On screen: References become a dependency graph. It sets the order.*

> The order of the blocks in the file does not matter. From the references, Terraform builds a dependency graph, and the graph decides.

**2:06.2**  room 17.2 s, 37 words (about 16.1 s)
*On screen: Apply walks the graph, building in parallel where it can.*

> That is what apply did at the start: it walked the graph. Whatever has no pending dependency is created at once, in parallel: the network and the bucket, then the subnet and the firewall, then both servers.

**2:23.5**  room 10.6 s, 19 words (about 8.3 s)
*On screen: Destroy walks the same graph in reverse.*

> And terraform destroy walks the same graph in reverse, so nothing is removed while something still depends on it.

## Plan  (2:34 to 3:29)

**2:34.5**  room 18.5 s, 40 words (about 17.4 s)
*On screen: terraform plan previews every change before it happens.*

> Now the same run again, one step at a time. First, terraform init downloads the provider. Then, before touching anything, terraform plan compares what you declared with what exists: six resources to add. It is a preview, like a diff.

**2:53.0**  room 11.5 s, 24 words (about 10.4 s)
*On screen: terraform apply makes the calls and records what it created.*

> terraform apply then makes those calls. And for each resource, it records the ID of the real object in a file called the state.

**3:04.6**  room 10.7 s, 22 words (about 9.6 s)
*On screen: The state maps each block to a real object.*

> The state is Terraform's memory. It is how it knows that this block in your code is that server in the cloud.

**3:15.3**  room 14.1 s, 27 words (about 11.7 s)
*On screen: Run it again and nothing changes: the same file gives the same result.*

> Apply again, and there is nothing to do. Code, state and cloud agree. You can apply the same file a hundred times and get the same result.

## Change  (3:29 to 4:10)

**3:29.8**  room 15.2 s, 31 words (about 13.5 s)
*On screen: Change the file: the plan shows only the difference.*

> To change the infrastructure, you change the file. Two servers become three. The plan shows exactly one resource to add, and leaves the other six alone. Apply, and it is built.

**3:45.0**  room 10.3 s, 21 words (about 9.1 s)
*On screen: Some changes update a resource in place.*

> Some changes can be made in place. A bigger instance type is an update: same servers, new size, after a restart.

**3:55.3**  room 15.4 s, 27 words (about 11.7 s)
*On screen: Others force a replacement: destroy, then create.*

> Others cannot. A new machine image forces a replacement: Terraform destroys each server and creates a new one. The plan tells you which, before you say yes.

## Drift  (4:10 to 4:42)

**4:11.1**  room 11.1 s, 23 words (about 10.0 s)
*On screen: Someone changes the cloud by hand: that is drift.*

> Now someone changes a server by hand, in the cloud console. The real infrastructure no longer matches the file. This is called drift.

**4:22.2**  room 10.2 s, 21 words (about 9.1 s)
*On screen: Every plan first reads the real resources.*

> The next plan notices. Every plan starts by reading the real resources, and comparing them with the state and the code.

**4:32.5**  room 10.4 s, 18 words (about 7.8 s)
*On screen: Apply puts the cloud back in line with the file.*

> It proposes to put the server back the way the file says. Apply, and the drift is gone.

## Team  (4:42 to 5:13)

**4:43.3**  room 14.2 s, 30 words (about 13.0 s)
*On screen: A team keeps the state in a shared backend.*

> In a team, the state cannot live on one laptop. It goes in a shared backend, like an S3 bucket, where everyone and your CI pipeline read the same state.

**4:57.5**  room 16.2 s, 32 words (about 13.9 s)
*On screen: The state is locked while someone applies.*

> Turn on the lock file, and the state is locked while someone applies. If two people run apply at the same time, the second one is refused, instead of corrupting the state.

## Envs  (5:13 to 5:46)

**5:14.2**  room 8.1 s, 16 words (about 7.0 s)
*On screen: Wrap the blocks in a module, with inputs.*

> Finally, wrap those five blocks in a module, with the number of servers as an input.

**5:22.3**  room 14.1 s, 30 words (about 13.0 s)
*On screen: The same code builds three environments, each with its own state.*

> Now the same code builds dev, with one server. Then staging, with two servers. And production, with four. Three environments, three state files, one definition, and nothing done by hand.

**5:36.4**  room 10.1 s, 18 words (about 7.8 s)
*On screen: Describe what you want. Review the plan. Let the cloud match the file.*

> That is Terraform: describe the infrastructure you want, review the plan, and let it make the cloud match.

## Outro  (5:46 to 5:58)

**5:46.6**  room 11.7 s, 4 words (about 1.7 s)

> Thank you for watching.
