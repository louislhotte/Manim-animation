# Voice-over script: Mixed-Integer Programming

Film length **8:55** (535.8 s), 31 lines, 1090 words. Timecodes are from the 1080p60 render; every line starts when its caption appears.

*Room* is the time until the next line starts. The pacing assumes 138 words a minute, so a line of *n* words wants about n / 2.3 seconds. A line marked **TIGHT** has less than that.

`voiceover.srt` holds the same lines as subtitles: load it next to the video to read along while recording.

## Intro  (0:00 to 0:13)

**0:00.0**  room 14.0 s, 24 words (about 10.4 s)

> Mixed-integer programming: how a solver finds the best plan among billions, and proves it. Our example: delivering meals in Paris, on a Friday night.

## Night  (0:13 to 0:58)

**0:14.0**  room 12.0 s, 25 words (about 10.9 s)
*On screen: Friday, 8 p.m. in Paris: 104 couriers, 403 orders.*

> Friday, eight p.m., in Paris. One hundred and four couriers are on their bikes, and four hundred and three meals are waiting in restaurant kitchens.

**0:26.0**  room 17.2 s, 37 words (about 16.1 s)
*On screen: Who delivers what, and in which sequence?*

> Who should deliver what, and in which sequence, so that the couriers earn the most in the next hour? Just handing out the orders can be done in more ways than there are atoms in the universe.

**0:43.2**  room 15.8 s, 29 words (about 12.6 s)
*On screen: A solver finds the best plan, and proves it. Follow one courier.*

> A solver such as Gurobi finds the best plan, district by district, in under a minute, and proves that nothing better exists. To see how, follow one courier: Léa.

## Hour  (0:58 to 1:58)

**0:59.4**  room 16.8 s, 36 words (about 15.7 s)
*On screen: Léa has one hour, and eight orders around her.*

> This is Léa. She has one hour left, and eight orders around her. Each pays a fee, and each can only be delivered inside its own window: after the meal is ready, before the customer's deadline.

**1:16.2**  room 15.4 s, 33 words (about 14.3 s)
*On screen: A course: some of the orders, in a sequence.*

> She cannot deliver them all. A course is a choice: which orders, in which sequence. Her instinct: take the best-paid order that still fits, then the next. That course earns eleven euros ninety.

**1:31.6**  room 14.6 s, 31 words (about 13.5 s)
*On screen: Trying every sequence finds the best course: 24.40 euros.*

> Is there better? With eight orders, a computer can try every sequence: one hundred and nine thousand six hundred of them. The best one earns twenty-four euros forty. Twice as much.

**1:46.2**  room 12.3 s, 23 words (about 10.0 s)
*On screen: With twenty orders, trying them all takes 200,000 years.*

> But this does not scale. With twenty orders, there are six billion billion sequences: at a million per second, two hundred thousand years.

## Model  (1:58 to 3:25)

**1:59.1**  room 17.6 s, 38 words (about 16.5 s)
*On screen: Decisions: one switch per possible ride, 0 or 1.*

> So we stop searching by hand, and describe the problem instead. First, the decisions. For every possible ride, from one stop to an order, a variable that is zero or one: skip it, or ride it. Sixty-four switches.

**2:16.7**  room 10.2 s, 21 words (about 9.1 s)
*On screen: The goal: the fees of the rides she takes, as high as possible.*

> Second, the goal: add up the fee of every order she rides to, and make that sum as large as possible.

**2:26.9**  room 12.8 s, 27 words (about 11.7 s)
*On screen: The rules: one start, each order once, no ride from nowhere.*

> Third, the rules. A courier starts one course at most. An order is delivered at most once. And she can only leave a stop she has reached.

**2:39.8**  room 12.8 s, 27 words (about 11.7 s)
*On screen: And time: each order gets the minute it is delivered.*

> The last rule is about time. Every order gets one more variable: the minute it is delivered. Draw time as height: each order's window becomes a bar.

**2:52.6**  room 14.1 s, 30 words (about 13.0 s)
*On screen: Each delivery comes one ride after the last, inside its window.*

> If she rides from one order to the next, the second minute comes at least one ride later. And every delivery must fall inside its window, before the hour ends.

**3:06.8**  room 18.4 s, 37 words (about 16.1 s)
*On screen: A mixed-integer program. One call solves it.*

> Whole-number decisions, continuous times, rules that can be written as linear inequalities: a mixed-integer program. One call, optimize, and the solver answers: twenty-four euros forty. The same course as trying everything, in two hundredths of a second.

## Relax  (3:25 to 4:21)

**3:25.7**  room 14.2 s, 30 words (about 13.0 s)
*On screen: First, simplify: rides that can never fit the clock go.*

> How can a solver be sure, without trying every sequence? It starts by simplifying. Of the sixty-four possible rides, twenty-eight can never fit the clock. Remove them: thirty-six switches remain.

**3:39.8**  room 18.1 s, 39 words (about 17.0 s)
*On screen: Then relax: every switch may take any value from 0 to 1.*

> Then it cheats. Let every switch become a dimmer, anywhere between zero and one: half of this ride, three quarters of that one. With no yes-or-no left, the problem is easy: a linear program, solved in half a millisecond.

**3:57.9**  room 23.6 s, 49 words (about 21.3 s)
*On screen: Its value is a ceiling: no real course can earn more.*

> The relaxed plan claims thirty-three euros ninety. It is not a real course: half a ride earns half its fee, and only half obeys the clock. But every real course is still allowed in the relaxed problem, so no real course can earn more. That number is a ceiling.

## Branch  (4:21 to 5:36)

**4:22.6**  room 17.6 s, 38 words (about 16.5 s)
*On screen: Branch: take one fractional ride, or leave it.*

> Now pick one fractional ride, and split the problem in two. In one branch, she must take that ride. In the other, she must leave it. Each branch is relaxed again, and gets a ceiling of its own.

**4:40.2**  room 18.9 s, 41 words (about 17.8 s)
*On screen: Dive until a plan comes out whole: a real course, a floor.*

> Keep splitting, diving down one side. Some branches are dead ends: no plan fits. Then a relaxed plan comes out whole, only zeros and ones: a real course, worth seventeen euros fifty. That is a floor: the best course so far.

**4:59.2**  room 18.9 s, 41 words (about 17.8 s)
*On screen: Bound: a branch whose ceiling is under the floor is cut.*

> From here, always open the branch with the highest ceiling. Better courses appear, and the floor rises: twenty-two forty, twenty-three seventy, twenty-four forty. And a branch whose ceiling is under the floor cannot hide anything better: cut it, without looking inside.

**5:18.1**  room 18.8 s, 38 words (about 16.5 s)
*On screen: Floor and ceiling meet: 24.40 euros, proven optimal.*

> The ceiling comes down, the floor comes up. When they meet, the search is over: twenty-four euros forty is proven optimal. One hundred and sixteen small problems, and no branch is left that could hide a better course.

## Solver  (5:36 to 7:45)

**5:37.4**  room 28.9 s, 64 words (about 27.8 s)
*On screen: A cut: a rule every real course obeys, and the relaxed plan breaks.*

> A real solver adds two accelerators. First, cutting planes. Our relaxed plan claimed six orders. But six deliveries take more than sixty minutes, and the last deadline is at fifty-nine: no real course fits more than five. Add that rule, at most five, and the ceiling drops from thirty-three ninety to twenty-nine twenty, without a single branch. A solver finds such rules by itself.

**6:06.4**  room 16.3 s, 35 words (about 15.2 s)
*On screen: A heuristic: a quick real course, an early floor.*

> Second, heuristics: quick guesses at real courses, to raise the floor early. Even a simple rule, always the order that can be delivered soonest, gives a floor of seventeen euros ten before the search begins.

**6:22.7**  room 22.4 s, 49 words (about 21.3 s)
*On screen: Gurobi's log tells the same story.*

> Gurobi does all this, and narrates it in its log. Presolve removes forty-four of the seventy-three columns, its word for variables. The root relaxation gives a first ceiling, already lower than ours: thirty-two seventy-nine. Lines marked H are heuristic floors. Then cutting planes take the ceiling down to twenty-seven.

**6:45.1**  room 21.1 s, 46 words (about 20.0 s)
*On screen: Incumbent, best bound, gap: floor, ceiling, distance.*

> Three columns tell the story. Incumbent is the floor. Best bound is the ceiling. Gap is the distance between them, as a share of the floor. Here it closes at the very first node, without a single branch: our one hundred and twenty-nine nodes became one.

**7:06.2**  room 13.7 s, 29 words (about 12.6 s)
*On screen: A whole district: 8 couriers, 32 orders, 1,248 switches.*

> Now a whole district, the eleventh arrondissement: eight couriers, thirty-two orders, one thousand two hundred and forty-eight switches. Same model, same call. Here is the search, in real time.

**7:19.9**  room 25.4 s, 53 words (about 23.0 s)
*On screen: Gap closed: proven optimal. Stopped early, a solver still reports its gap.*

> More than thirty-one thousand nodes in three point four seconds, for a problem with three thousand billion billion billion ways to hand out its orders. The gap is closed: this plan is proven optimal. Stop a solver earlier, and the gap still tells you how far from the best you can possibly be.

## City  (7:45 to 8:44)

**7:45.8**  room 19.4 s, 42 words (about 18.3 s)
*On screen: Twenty arrondissements, twenty models, all solved to proven optimality.*

> Back to Friday night. Each courier serves one arrondissement, so the same model runs once per arrondissement: twenty models, more than ten thousand switches in all. Gurobi solves them one after the other in fifty-five seconds, and every one is proven optimal.

**8:05.1**  room 13.4 s, 27 words (about 11.7 s)
*On screen: 20:00 to 21:00: the couriers ride the plan.*

> And the couriers ride. One hour later: three hundred and seventy-eight of the four hundred and three meals delivered, two thousand one hundred and sixty euros earned.

**8:18.5**  room 12.0 s, 25 words (about 10.9 s)
*On screen: Same couriers, same hour: 46 more meals than the obvious rule.*

> The obvious rule, always sending the order that can be delivered soonest, would have delivered forty-six meals fewer, and earned the couriers fifteen percent less.

**8:30.5**  room 13.6 s, 26 words (about 11.3 s)

> That is mixed-integer programming. You describe the plan you want: decisions, a goal, rules. The solver relaxes, branches and bounds, until it can prove its answer.

## Outro  (8:44 to 8:55)

**8:44.1**  no narration (11.7 s).
