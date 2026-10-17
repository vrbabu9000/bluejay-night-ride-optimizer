# How the Blue Jay Night Ride operates: TransLoc OnDemand, dispatch and the Lyft overflow

**Version 1.0, 2 Oct 2026.** This is a research document for Team FourSight. It describes how the service works, so that the simulator can be modelled on it. It is **not** the scenario definition, which is on hold until the team agrees on this document.

## How to read this document
Every claim carries an evidence grade:

| Grade | Meaning |
|---|---|
| **JHU** | Stated by Johns Hopkins (Transportation Services pages, Hub announcements). Dates matter: rules changed between 2018 and 2026 |
| **VENDOR** | Stated by TransLoc (product pages, press releases, its engineering blog) |
| **PRESS** | Student newspapers or other press, including officials quoted there |
| **PEER** | Practice at other universities. It shows what is common, not what Hopkins does |
| **DATA** | Our April 2026 evidence pack (`docs/evidence/`) |
| **INFERRED** | Our reasoning from the above. The reasoning is stated, and we must be ready to defend it |
| **REPORTED** | Said to the team in conversation (not written down) |
| **UNKNOWN** | Not found in any public source. These become the assumptions in section 9 |

**Sources.** Section 12 lists them, accessed 2 Oct 2026. Text snapshots are in `docs/evidence/context/transloc_sources/` (gitignored). Most JHU pages block automated fetches, so they were read through Internet Archive snapshots; each snapshot date is given.

---

## 1. Summary: ten findings that matter for the model

1. **Assignment is automatic, by TransLoc's scheduling engine.** Riders book; the software assigns the ride to a van and orders that van's stops; the driver's tablet shows where to go next (VENDOR). We found **no public evidence that TransLoc drivers can accept or reject rides**. The team's contact describes vans in an area being offered the ride to accept or decline (REPORTED). Section 6 weighs the two accounts; we keep driver response as a variant.
2. **The engine re-plans the whole fleet repeatedly.** In TransLoc's own 2016 description, it re-solves on every new ride, every cancellation, every driver-reported no-show, **and every two minutes**. Each time it can change which van serves which ride and the order of stops (VENDOR, 2016; the current version is UNKNOWN). **The status quo is therefore already a "coordinating" dispatcher, not a greedy one.** This changes our research question (section 10).
3. **The objective trades off wait, ride time and miles.** The weights are not public. TransLoc says the wait-time penalty can grow faster than linearly (VENDOR). Hopkins states a **"safety first" policy**: a van with spare seats is often sent to pick up waiting riders before it drops off the riders on board (JHU). That is consistent with wait being weighted heavily against ride time.
4. **Hopkins publishes service targets, and they are soft.** For Homewood: pickup within 15 minutes of the request and rides no longer than 20 minutes, with up to 20 minutes for pickup at busy times. For East Baltimore: averages of 12 minutes for wait and ride, with goals of at most 20 and 25 minutes (JHU 2026). April's P90 wait (about 17–21 min) and P90 ride (about 24 min) exceed the Homewood targets (DATA), so they are **targets, not hard limits**.
5. **Lyft overflow is a human dispatcher's decision.** In peak hours a dispatcher may move a still-pending van ride to Lyft and book the Lyft for the rider (JHU). The rider needs no Lyft app and is told by text message.
   - Criteria named in 2018: group size (5 or more always gets a van, since a Lyft seats 4), location and wait time (PRESS).
   - In 2018 the dispatcher asked whether the rider would accept a Lyft (JHU).
   - Students describe the rule as "a Lyft if the van doesn't arrive within 15 minutes" (PRESS 2026).
6. **In the dashboard, a Lyft transfer most likely shows up as a "Canceled" van ride.**
   - Daily Lyft riders track daily cancellations (r = 0.88), and Hopkins' own slide says many cancellations become Lyfts (DATA).
   - At April's party size, Lyft hand-offs would explain **roughly a third of all cancellations** (about 260 of 795 a day; plausible range 23–46%, depending on Lyft party size) (INFERRED).
   - The remaining two thirds or so are rider cancellations, rebookings and duplicates. They are not separated.
7. **"Denied" is essentially never used at Homewood** (about 0 a day in April, DATA). The system takes every in-area request, and overload shows up as long waits, cancellations and Lyft transfers, not refusals (INFERRED).
8. **No-show rule: the van waits up to 3 minutes, then the driver marks a no-show.** The rider gets a message, and the scheduler re-plans (JHU and VENDOR). No-shows were steady in April, at 4.7% of requests (DATA). Peer programs wait 2–5 minutes (PEER).
9. **The 6 pm van count probably includes East Baltimore vans.**
   - The vehicle chart is filtered to "All services".
   - The East Baltimore Blue Jay Shuttle also runs on TransLoc, from 5:30 pm to midnight (JHU), and the count drops by 5.6 vans exactly at midnight (DATA).
   - So Homewood probably had about 22 vans at 6 pm, not 27.6 (INFERRED). If so, Homewood served about 7.7 rides per van-hour, not 6.2.
10. **The vans are larger than we assumed.** Hopkins described its Night Ride vans as **14-seat** (PRESS 2018, quoting the Director of Transportation Services). Bookings are capped at **5 riders** (JHU). Our assumed capacity of 4 (D-22) is likely wrong for Homewood.

---

## 2. TransLoc, the company
| Year | Event | Grade |
|---|---|---|
| 2004 | Founded by four NC State computer-science students and graduates (Josh Whiton, Dominique Bischof, Jesse Lovelace, Justin Harris). The first product was real-time bus tracking for NC State's Wolfline. TransLoc gives 2004 as its founding year; one 2016 article says 2005 | VENDOR, PRESS |
| 2012 | TransLoc Rider app (real-time arrivals) | PRESS |
| Aug 2015 | **TransLoc OnDemand** launched: app booking with automatic dispatch, aimed first at university Safe Ride programs | VENDOR |
| 2015–16 | Early OnDemand results: NYU (+32% riders served per day, −15% wait), Emory (+52–53% rides per week, −49% dispatcher calls, no added vehicles); 23 universities on OnDemand by Dec 2016 | VENDOR, PRESS |
| 2016 | In-advance booking added; Uber trip-planning integration in the Rider app (Memphis, Raleigh-Durham) | VENDOR |
| Jan 2018 | **Acquired by Ford** (Ford Smart Mobility), pitched as technology for city-owned microtransit | VENDOR |
| Sep 2018 | Over 40 cities on its "agency-owned microtransit" model (e.g. SacRT SmaRT Ride) | VENDOR |
| Mar 2022 | **Sold to Modaxo**, the people-transport division of Constellation Software. At that time TransLoc served over 1,500 transport providers and about 600 million rides a year across all products | VENDOR |
| 2026 | Product lines: fixed-route tracking (CAD/AVL), OnDemand microtransit, rider and driver apps, GTFS and data tools, passenger counters, announcements. Headquarters in Durham, NC | VENDOR |

**Why it matters.** TransLoc is a software vendor. It does not operate vehicles. Hopkins owns the vans, employs or contracts the drivers and dispatchers, and sets the service rules; TransLoc supplies the apps, the scheduling engine and the dashboards. The April PDF we digitized consists of TransLoc dashboards, plus one PowerBI panel from Hopkins' own system, which is the only place Lyft appears.

---

## 3. TransLoc OnDemand: how the platform works

### 3.1 Components
| Component | What it does | Grade |
|---|---|---|
| **Rider app / web** (`ondemand.transloc.com`) | Rider enters pickup and drop-off and the number of riders. Rider sees an ETA once the ride is assigned, can track the van, gets push notifications (approaching, arrived), and can cancel | VENDOR, JHU, PEER |
| **Phone booking** | A dispatcher books the ride for the caller and gives an ETA (Hopkins: 410-516-8700) | JHU |
| **Scheduling engine** | Assigns rides to vehicles and orders each vehicle's stops (section 3.2) | VENDOR |
| **Driver app** (tablet or phone) | Shows the next stop with turn-by-turn or "next stop" navigation. Driver marks arrive / picked up / dropped off / no-show. It has an interactive wait timer where the agency sets a wait standard (since 2021), a "rider can't see you" message within 200 m of the pickup, automatic proximity alerts to riders (2019), and the ability to add walk-up riders by entering passenger count and destination (2019) | VENDOR |
| **Dispatcher / operations console** | Watch pending, in-progress and completed rides; book call-in rides; monitor vehicles. Manual override features (reassigning, forcing an order) are **not publicly documented** | VENDOR (partial); details UNKNOWN |
| **Reporting dashboards** | Rides by status, wait and ride-time percentiles, vehicles in service, origin and destination heat maps. This is the source of our April PDF | VENDOR, DATA |
| **Router** | Road travel times between stops. In 2016, TransLoc's own A* router on OpenStreetMap data (it was considering OSRM). The current router is UNKNOWN | VENDOR |

### 3.2 The scheduling engine
Source: a 2016 post on TransLoc's engineering blog by one of its software engineers (archived copy, April 2018). Everything in this section is VENDOR as of 2016; whether today's engine still works this way is UNKNOWN.

**Inputs**
- **Vehicles:** current location, current load and seat capacity.
- **Rides:** origin, destination, number of passengers, a desired time (for advance bookings only), and a list of **candidate vehicles** produced by another part of the system. How candidates are chosen (zones, a radius, vehicle type?) is not described. This may be the "vehicles in that region" in the contact's account.

**Decisions:** which vehicle serves each ride, and in what order each vehicle makes its stops. A pickup always comes before its drop-off.

**Method:** **simulated annealing**, a randomized local search. A move either reassigns a ride to another vehicle or moves a stop to a new position in the order. Millions of candidate plans are scored per solve.

**Score to minimize:** a weighted mix of
- passenger wait time;
- passenger ride time;
- vehicle mileage.

The weights are not public. The terms need not be linear: TransLoc's own example prefers cutting 1 minute from a 10-minute wait over cutting 2 minutes from a 5-minute wait. Constraints named: precedence (pickup before drop-off), capacity, and the candidate-vehicle list. **No hard limit on wait or ride time is mentioned.**

**When it runs:**
- a new ride is booked;
- a ride is cancelled;
- a driver reports a no-show;
- **every 2 minutes**, to refine the plan.

Each solve re-plans the whole fleet, so **a ride that has been assigned but not yet picked up can move to another van**, and stop orders can change. The engine logs its estimates so they can be compared with what actually happened.

**Advance bookings:** idle time is spread between stops so that each van arrives as close as possible to the requested times. The blog describes solving this with isotonic regression; it is not relevant to on-demand Night Ride.

**Scale:** a 12-ride, 1-vehicle example solved repeatedly to the same plan in under 15 seconds. The service's early record was 60,000 passengers with an average wait of 8 minutes.

**What this means for us (INFERRED).** TransLoc's engine is a **rolling-horizon re-optimizer with reassignment**. It is close to our planned player C, a periodic joint optimization, run as a heuristic rather than an exact MILP, every 2 minutes plus on events. It is not the greedy "insert and never move" policy (our A). Section 10 draws the consequences.

### 3.3 Life cycle of a ride and its statuses
```mermaid
stateDiagram-v2
    [*] --> Requested: rider app / web / phone (dispatcher)
    Requested --> Pending: accepted into the system (in area, in hours, group ≤ 5)
    Requested --> Denied: refused (≈0 per day at Homewood in April)
    Pending --> Assigned: engine assigns a van + ETA (may change at each re-plan)
    Assigned --> Pending: re-plan moves the ride (internal)
    Pending --> TransferredToLyft: dispatcher moves it (peak, party ≤ 4)
    Assigned --> TransferredToLyft: dispatcher moves it
    Pending --> Canceled: rider cancels
    Assigned --> Canceled: rider cancels
    Assigned --> Arrived: van at pickup; rider alerted
    Arrived --> OnBoard: rider boards within 3 min
    Arrived --> NoShow: 3-min wait expires; driver marks no-show
    OnBoard --> Completed: dropped off
    TransferredToLyft --> LyftCompleted: Lyft trip (outside TransLoc)
    Completed --> [*]
    Canceled --> [*]
    NoShow --> [*]
    Denied --> [*]
    LyftCompleted --> [*]
```

| State | Evidence | Notes |
|---|---|---|
| Pending | PEER: University of South Carolina says a booked ride stays pending until assigned to a driver | How long rides stay pending, and whether the engine holds a ride back on purpose, is UNKNOWN |
| Assigned (ETA) | VENDOR, PEER (Duke: assigned to a nearby van with an ETA) | The ETA can change at each re-plan |
| Arrived, then the 3-min wait | JHU, VENDOR | The app's message reads "the driver has indicated they cannot see you". Hopkins calls this standard wording from its dispatch provider |
| No-show | JHU, VENDOR | Ends the ride; the rider is told; the engine re-plans |
| Canceled | DATA | **Includes at least:** rider cancellations and (INFERRED) dispatcher cancellations for Lyft transfers. **May include:** duplicates and rebookings. The parts are not separated |
| Denied | DATA (≈0) | Its definition is UNKNOWN. Out-of-area or out-of-hours requests are probably blocked in the app before booking (INFERRED) |
| Lyft trip | JHU, DATA | Counted outside TransLoc, in Hopkins' PowerBI (Van + Lyft riders) |

### 3.4 Who decides what
| Decision | Who | Grade |
|---|---|---|
| Accept a request into the system | System: area, hours, eligibility, group of 5 or fewer | JHU, INFERRED |
| Which van, and in what stop order | **Scheduling engine**, automatically | VENDOR |
| Change an assignment | Engine at each re-plan (VENDOR, 2016). Dispatcher overrides UNKNOWN | VENDOR, UNKNOWN |
| Drive the route | Driver follows the app | VENDOR |
| Accept or reject a ride | **Not found** for TransLoc drivers. The contact says yes (section 6) | REPORTED vs VENDOR |
| No-show | Driver, after the wait timer (3 min at Hopkins) | JHU, VENDOR |
| Move a ride to Lyft | **Dispatcher**, at peak times | JHU |
| Cancel | Rider (app or phone) | JHU, VENDOR |

### 3.5 What the agency configures
Known:
- service hours;
- service area (geofence);
- eligibility (Hopkins: a JH email address and a 10-digit phone number);
- maximum group size per booking (5);
- the wait-timer standard (3 min);
- the fleet in service (who logs in, and when).

Not public:
- the score weights;
- any hard maximum wait or ride time inside the engine;
- how candidate vehicles are chosen;
- any pickup-window settings;
- dispatcher permissions.

Hopkins' published 15/20-minute "service parameters" may be engine settings, or only public targets. **UNKNOWN.**

### 3.6 TransLoc runs the same kind of study we are building
For a 2020 microtransit pilot in Illinois, TransLoc used a **simulator that runs the production scheduling algorithm** (VENDOR, in the agency report).
- **Inputs:** simulated ride requests (request time, origin, destination; drawn from census density when nothing better exists) and "service parameters" (number of vehicles, hours, capacity), each varied over a range.
- **Outputs:** average and 90th-percentile wait, average ride time, and the share of rides under 15 minutes.

The questions it answered are ours: how many rides per vehicle, what happens if demand doubles, and how service quality trades against cost. **This supports our design** (synthetic demand matched to aggregates, plus a referee engine and players). It also tells us **which outputs the vendor and agency look at**.

---

## 4. The Hopkins Blue Jay Night Ride (Homewood)

### 4.1 Timeline
| When | What changed | Grade |
|---|---|---|
| Fall 2017 | Ridership about 80% above earlier years: nearly **10,000 riders a month** | JHU (Hub, 2018) |
| Jan 2018 | Fleet expanded to **12 vans**, new drivers, a larger dispatch team, improved TransLoc app; service 5:30 pm–3:45 am. **Lyft added on Friday and Saturday nights.** Wait goal: **10 minutes**. A dispatcher may ask whether the rider will take a Lyft instead; the Lyft waits up to 5 minutes | JHU (Hub) |
| Feb 2018 | Dispatcher chooses between Lyft and a van: **5 or more riders always get a van** (a Lyft seats 4, a van **14**); for 4 or fewer, location and wait time decide | PRESS (News-Letter, quoting the Director of Transportation Services) |
| Aug 2019 | Evening fixed routes restructured (Homewood Route, more frequent Brody shuttle); **Night Ride extended to the Peabody Institute** (6 pm–3:45 am); app notifications become push messages; riders sent to Lyft still get texts | JHU (Hub) |
| Aug–Sep 2022 | East Baltimore Blue Jay Shuttle launched (5–9 am and 5:30 pm–midnight, with Lyft). Homewood Night Ride radius **reduced** (it had served the Inner Harbor). **Peabody re-merged into the Homewood Night Ride area** (Sep 18). Students reported longer waits; the university cited technical problems from growth | PRESS (News-Letter 2022), JHU |
| 2023 (archived page) | Rules as in 4.2: 3-minute van wait, group of 5 or fewer, "safety first", dispatcher Lyft transfers at peak, 3-minute Lyft wait. In term time, the Peabody area is roughly 20th St (north), Guilford Ave / South St (east), Pratt St (south), Howard St (west) | JHU |
| Oct 2025 | Student survey (small sample, not a random sample): 40% agree vans arrive promptly, 33% disagree; complaints of long, indirect rides and app ETAs that don't match. Reported total of 25–30 min to get a van or Lyft at busy times | PRESS |
| Jul 2026 (archived page) | Current rules (4.2) | JHU |
| Apr 2026 | 44,374 riders in the month (van + Lyft), **24.5% by Lyft** | DATA |

Ridership grew about **4.4×** from fall 2017 (about 10k riders a month) to April 2026 (44k). That is an order-of-magnitude comparison only: the months, the definitions and the inclusion of Lyft differ.

### 4.2 Current service rules (JHU, archived 22 Jul 2026)
- **Hours:** requests accepted from 6 pm; requests made before 2 am are honoured, so service runs past 2 am to finish them.
- **Booking:** TransLoc app (needs a 10-digit phone number and a .jh/.jhu/.jhmi email), the web, or phone to a dispatcher.
- **Area:** curb-to-curb within a zone close to the Homewood campus. In term time it is combined with the Peabody area. **Both ends of the trip must be inside the zone.**
- **Group:** at most **5** per booking; larger groups split. Members with different destinations should book separate rides from the same origin.
- **Guests:** "a reasonable number", typically up to four or one family group.
- **Arrival and wait:** the rider is alerted when the van arrives, and **the van waits up to 3 minutes**, then leaves for its next stop.
- **Order of service:** "safety first, then convenience". Vans with space often go to waiting pickups before heading to a drop-off. Riders should expect indirect trips.
- **Service parameters:** pickup within **15 minutes** of the request, ride **no longer than 20 minutes**; at busy times up to **20 minutes** to arrive. **Dispatchers track the vans; if a ride can't be provided in time, a free Lyft is dispatched.**
- **Lyft:** at peak times dispatchers **may transfer a pending ride** to Lyft. The rider gets texts and doesn't need the Lyft app. The Lyft driver waits up to **3 minutes**.
- **Vans:** three-digit fleet numbers, power sliding doors, cameras and TransLoc GPS.

The East Baltimore service (same brand, separate area) publishes **averages of 12 minutes for both wait and ride, with goals of at most 20 and 25 minutes**. Those are the 20/25 numbers our decision D-04 used, so they belong to **East Baltimore, not Homewood**.

### 4.3 Fleet, staffing and dispatch
- **Fleet:** 12 vans in 2018 (JHU). We found no current public figure.
- **April 2026 "vehicles in service" (All services), by hour (DATA):** 27.6 at 18:00, 27.3, 24.6, 19.4, 16.7, 16.6, then **11.1 at midnight**, 9.3 at 1 am and 4.4 at 2 am. The largest hourly drops are at 21:00 (−5.2) and **00:00 (−5.6)**.
- **The 6 pm count likely includes East Baltimore (INFERRED).**
  - The East Baltimore evening service ends at midnight, the time of the 5.6-van drop.
  - So it likely contributes about 5–6 vans to the 6 pm count, leaving about **22 Homewood vans at 6 pm**.
  - The 21:00 drop (−5.2) could be Homewood shift ends, or other services ending (the Giant Night Ride fixed route runs 6–10 pm).
  - **Not verified:** the chart can't be split by service.
- **Drivers:** "University-owned" vans (PRESS 2026). Whether drivers are Hopkins staff or contractors is UNKNOWN. (The separate Homewood-Peabody-JHMI bus route is run by a contractor, Academy, with its own dispatch line.)
- **Dispatch office:** staffed during service hours. It takes phone bookings, answers ride-status questions, and decides on Lyft transfers. The number of dispatchers on duty is UNKNOWN.

### 4.4 The Lyft overflow in detail
- **How:** the dispatcher books the Lyft for the rider. Since 2018 Hopkins has had "Lyft dispatch tools"; Lyft sells a web booking portal (Lyft Concierge) for exactly this, with ride details texted to a rider who doesn't use the app (PEER/VENDOR: the Lyft for Business product page). That Hopkins uses Concierge itself is INFERRED.
- **When:**
  - "peak service hours" (2026) or "if a ride cannot be provided in a timely manner" (2026); originally Fridays and Saturdays only (2018);
  - students describe it as after 15 minutes without a van (PRESS 2026), or 10–15 minutes (a student blog);
  - an Oct 2025 article reports a department aim of a Lyft pickup within 15 minutes of the request (PRESS).
- **Who goes to Lyft:** groups of 4 or fewer, by location and expected wait (PRESS 2018). In 2018 the rider was asked first; whether consent is still asked is UNKNOWN.
- **What the rider sees:** texts with car make, model, colour and plate; a 3-minute driver wait.
- **What the data show (DATA):**
  - Lyft carried 24.5% of April riders (10–46% by day);
  - daily Lyft riders move with daily van cancellations (r = 0.88; 0.55 Lyft riders per extra cancellation);
  - Lyft does not move with van riders (r = −0.09). That fits a rule triggered by **van congestion**, not by demand alone.
- **The Lyft trip itself:** pooling, routing and wait times are outside TransLoc and outside our data (UNKNOWN). The Lyft driver (a Lyft contractor) can accept or decline in Lyft's own system. That is the one place in this chain where drivers certainly accept or reject (INFERRED from how Lyft works).

### 4.5 What the April 2026 dashboards say about operations (DATA)
Each item is cross-checked with the rules above:
- **Supply-limited:** completions follow the fleet, not the requests (T1).
- **Waits:** the median is about 10–13 min and the P90 about 17–21 min against the 15-minute target. **Many requests would pass 15 minutes**, which fits a Lyft share near 25%.
- **Rides:** the median is about 10 min, but the P90 is 24 min against the 20-minute target. The long tail comes from routing, not distance: the longest direct drive is 13.6 min (T6). It fits the "safety first" ordering (pickups before drop-offs).
- **Cancellations:** 47% of requests, rising about 7 points per minute of median wait (T3). Part of this is the Lyft hand-off (finding 6).
- **No-shows:** 4.7% of requests, steady from day to day.
- **Denied:** about 0.
- **Apr 17**, the slow night: the longest waits and rides, the most Lyft riders and the fewest van completions.

---

## 5. Peer programs: how other campuses run night rides

| Campus | Service | Platform; vehicles | Hours | Pickup / no-show | Group | Overflow | Notable | Grade |
|---|---|---|---|---|---|---|---|---|
| **Johns Hopkins** (Homewood) | Blue Jay Night Ride | **TransLoc OnDemand**; university vans (14 seats in 2018) | 6 pm–2 am (+ finishing) | Curb-to-curb; **3 min** | ≤5 | **Dispatcher transfers to Lyft** at peak | Merged with the Peabody area in term; 15/20-min targets | JHU |
| **Columbia** | On-Demand Evening Shuttle | **Via** (app and drivers; cars) | Evening–3 am, start varies by season | Nearby corner or set point (walk); **2 min** | +1–2 guests (same O/D) | None found; rider sees an ETA "proposal" and books it | App-outage fallback: vans run a fixed route that riders flag down | PEER |
| **Penn** | Evening Safety Shuttle | Penn Transit app (vendor not stated) | 7:30 pm–3 am | **2026: on-campus trips moved to designated stops** (≤2-min walk); off-campus door-to-door | +2 guests | None found | The switch to stops cut average wait by about **5 min** and **reduced cancellations** | PRESS |
| **Northwestern** | Safe Ride | **Via** | 7 pm–3 am in term | Pickup point in the app; **2 min** | ≤2 | Won't book if the wait would exceed **90 min** | **Private rides only (no pooling)**; one end must be on campus | PEER |
| **NYU** | Safe Ride | **TransLoc OnDemand** (since 2015) | Night | **2 min** | — | — | +32% riders, −15% wait on switching to TransLoc | VENDOR, PEER |
| **Duke** | Duke Vans | **TransLoc OnDemand** (2022; replaced Ridecell) | 6:30 pm–2 am, Mon–Sat | Assigned to a nearby van with an ETA | — | — | 2.5-mile boundary | PEER |
| **Emory** | Safe ride | **TransLoc OnDemand** (2015) | — | — | — | — | +52% rides, −49% dispatcher calls | VENDOR |
| **UVA** | UTS OnDemand / SafeRide | **TransLoc**; university-run since 2024 | After bus hours | **Fixed "blue-light" stops** (50+); **3 min** | — | — | Average wait 8–10 min (official) | PRESS |
| **Pitt** | SafeRider | **TransLoc** + phone dispatcher | 9 pm–3 am | **5 min**; dispatcher calls back | — | — | First come, first served; a no-show who calls back goes to the end of the list; suspension after repeat no-shows | PEER |
| **Kansas** | SafeRide | TransLoc-style app | 10 pm–2:30 am | Snapped to bus stops within 0.1–0.2 mi; **3.5 min** | — | — | Suspensions for no-shows | PEER |
| **Old Dominion** | SAFE RIDE | **TransLoc** | 6 pm–2 am | **2 min** | Each member books separately | — | Not flag-down | PEER |
| **Rhode Island** | Rhody On-Demand | **TransLoc** + contractor Transdev | 5:30/6 pm–1 am | — | — | — | No-show suspensions after a 2024 spike | PEER |
| **Georgetown** | SafeRides | Vans | 8 pm–2/3 am | — | — | **Uber pilot: discounted Uber when the SafeRides wait passes 15 min** | Threshold-triggered TNC overflow | PRESS |

**Patterns across campuses**
1. **Four ways to run it:**
   - (a) university vans with vendor auto-dispatch, e.g. TransLoc: Hopkins, NYU, Duke, Emory, ODU;
   - (b) vans with a dispatcher-centred, queue-like process: Pitt;
   - (c) the whole service contracted to a platform with its own drivers: Via at Columbia and Northwestern;
   - (d) TNC vouchers, alone or as overflow: Georgetown's pilot, and Hopkins as a hybrid.
2. **Overflow comes in three styles:**
   - a dispatcher transfers the ride (Hopkins);
   - a voucher kicks in at a wait threshold (Georgetown's 15 min);
   - no overflow: the rider just sees a long ETA, or the request is refused beyond a cap (Northwestern, 90 min).
3. **Stops vs door-to-door:**
   - Penn (2026), UVA and Kansas consolidate pickups at stops;
   - Penn reports shorter waits and **fewer cancellations**, which is independent support for our T3 wait–cancellation link;
   - Hopkins is curb-to-curb.
4. **No-show timers:** 2–5 minutes (Hopkins 3).
5. **Pooling:** most programs pool. Northwestern does not (private rides only).
6. **Accept/reject:** in the platform-run services (Via), the **rider** accepts a proposed ETA. We found **no campus where university van drivers accept or reject offered rides**.

---

## 6. Accept/reject: two accounts, and how we'll handle them
**The contact's account (REPORTED):** when a request comes in, the vehicles in that region or radius get the option to accept or reject it. A van must also drop its current passengers before their ride time runs out, while not making the new rider wait too long.

**What the written sources say:**
- TransLoc describes **automatic dispatch** ("within seconds"), with the driver's tablet saying where to go and whom to pick up (VENDOR 2015–16).
- TransLoc presented manual dispatching, such as walkie-talkie coordination, as a thing of the past (VENDOR 2016).
- No TransLoc driver-app release note mentions accepting or declining (VENDOR).
- Peer TransLoc campuses describe rides being *assigned* (Duke, USC).
- The engine does take a list of **candidate vehicles** per ride (VENDOR 2016). That is close to "vehicles in that region".

**Ways to reconcile them (INFERRED):**
1. **The candidate list is the "radius".** The engine considers only some vans for each ride, and the account blends this with driver choice.
2. **Hopkins configures a confirmation step,** for example a driver acknowledgement before a ride is final. No source shows this for TransLoc, but agency settings aren't public.
3. **The account describes the Lyft leg,** where Lyft drivers do accept or decline, or the dispatcher's choice between van and Lyft.
4. **It describes the dispatcher's view of the plan:** the engine proposes, and the dispatcher can intervene.

The second half of the account matches the engine's score exactly. Riders on board versus the rider waiting is the wait-versus-ride-time trade-off, which Hopkins resolves "safety first", towards waiting riders.

**How we'll model it:** the default is automatic central assignment by a re-planning engine (best supported). **Driver response is a scenario variant**:
- a short response delay;
- a probability of declining, after which the ride goes back to the pool;
- a candidate radius.

If the variant changes results materially, we report it as a finding.

---

## 7. Our working model of a Night Ride (synthesis for framing)
| Actor | Information | Decisions | Behaviour in the model |
|---|---|---|---|
| **Rider** | Their own request and ETA | Book; cancel; be present or not | Books with a party of 1–5 inside the area. May cancel while waiting, more likely as the ETA or wait grows (T3, Penn). May not show (about 5%). May rebook (UNKNOWN) |
| **Scheduling engine** (TransLoc) | All open rides and all vans (positions, loads) | Assign rides and order stops; re-plan on events and every 2 min | Minimises weighted wait, ride and miles; a convex wait penalty; reassignment allowed until pickup; capacity and precedence are hard constraints |
| **Driver** | Next stop, wait timer | Drive, wait 3 min, mark no-show | Follows the plan. Variant: response delay or declining |
| **Dispatcher** | The whole board, ETAs, call-ins | Book phone rides; **transfer pending rides to Lyft** | Rule-based stand-in: in peak hours, transfer a pending ride (party ≤4) whose expected wait is above a threshold, after a reaction lag. Possibly limited by dispatcher capacity |
| **Lyft** | The transferred trip only | Lyft's own matching | Picks up after a Lyft wait, then drives direct (no pooling). Counted separately |
| **Service rules** | — | — | Hours 18:00–02:00 (finish the backlog); area; group ≤5; 3-min wait; soft targets 15/20 min |

**What each run reports:**
- the status counts: completed, canceled (rider vs Lyft transfer), no-show, denied;
- per-rider times: wait, pickup, drop-off, ride;
- Lyft trips;
- van-hours and miles.

These are exactly the categories in the April dashboard, so model and data can be compared.

---

## 8. What we can and cannot learn from public sources
**Settled enough to build on:**
- automatic central assignment with re-planning;
- the 3-minute wait and the no-show flow;
- a dispatcher-driven Lyft overflow at peak times;
- the 15/20 targets, which are soft;
- the safety-first ordering;
- the group cap of 5;
- 14-seat vans in 2018;
- the service area including Peabody in term;
- requests taken until 2 am.

**Not public, and probably never will be:**
- the engine's weights and its current algorithm;
- candidate-vehicle selection;
- the exact Lyft rule (threshold, lag, consent);
- what is inside "Canceled";
- how many Homewood vans are in service by hour;
- current van capacity;
- rider patience and rebooking.

These become the assumptions below. Each is varied, not hidden.

---

## 9. Assumptions register
Each line says what we don't know, what we assume, why, and how we'll test sensitivity. **S** = how sensitive we expect results to be (H/M/L). These feed the scenario definition once it is unblocked.

| ID | Topic | What we don't know | Default assumption | Basis | Variants to test | S |
|---|---|---|---|---|---|---|
| **AS-01** | Assignment | Who decides which van | Automatic central assignment by the engine | VENDOR | + driver response delay (0 / 30 / 60 s); + decline probability (0 / 10 / 25%) with re-pooling; candidate radius | H |
| **AS-02** | Re-planning | Current cadence and whether reassignment is allowed | Re-plan on every event and every 120 s; rides assigned but not picked up may move | VENDOR 2016 | 60 / 120 / 300 s; reassignment allowed vs not | H |
| **AS-03** | Engine objective | Weights for wait, ride and miles; their shape | Lexicographic or weighted: convex wait penalty > ride time > miles (safety first) | VENDOR, JHU | Wait-heavy vs ride-heavy weights; linear vs convex wait | H |
| **AS-04** | Engine method | Today's algorithm | A good heuristic (insertion + local search) standing in for TransLoc's annealing | VENDOR 2016 | Our exact MILP (C) as an upper reference | M |
| **AS-05** | Service targets | Hard limits or soft targets | **Soft:** 15-min pickup, 20-min ride (Homewood), used in the score and as reporting thresholds, not as hard constraints | JHU, DATA (April P90s exceed them) | Hard caps (as in D-04, 20/25) as a variant | H |
| **AS-06** | Lyft trigger | Threshold, timing and who qualifies | A pending ride with party ≤4 whose expected wait is over **15 min** is transferred after a **dispatcher lag**, during peak hours only | JHU, PRESS | Threshold 10 / 15 / 20 min; lag 0 / 2 / 5 min; consent probability 1.0 / 0.8; "peak" = whole night vs Fri–Sat vs when waits are high | H |
| **AS-07** | Dispatcher capacity | How many transfers per hour dispatchers can handle | Unlimited (no queue) | — | Cap of k transfers per 10 min | M |
| **AS-08** | Lyft service | Lyft wait and ride | Lyft pickup within 5–10 min (draw); direct ride at OSRM time × multiplier; unlimited Lyft supply | PRESS (target ≤15 min after request) | Lyft wait 5 / 10 / 15 min | L–M |
| **AS-09** | Rider cancellation | Patience distribution | Patience drawn once per request; hazard rises with the ETA shown and with time waited | DATA T3, Penn | Calibrated so that rider cancellations (not Lyft) ≈ 2/3 of "Canceled" | H |
| **AS-10** | What "Canceled" contains | Shares of rider cancellations / Lyft transfers / duplicates | Lyft transfers ≈ **1/3** of "Canceled" (range 23–46%) | INFERRED from DATA | The range | M |
| **AS-11** | Rebooking | Do riders rebook after cancelling or a no-show? | No rebooking (base) | — | Rebook probability 0.2 after a delay | M |
| **AS-12** | No-show | Probability and link to wait | 4.7% of requests no-show, independent of wait; the van waits 3 min | DATA, JHU | Probability rising with wait | L–M |
| **AS-13** | Denial | When requests are refused | Never, inside area and hours | DATA (≈0) | — | L |
| **AS-14** | Homewood fleet by hour | Vans in service | **About 22 at 6 pm**: the All-services 27.6 minus ~5.6 East Baltimore vans (from the midnight drop) | INFERRED | 22 / 25 / 27.6 | H |
| **AS-15** | Van capacity | Current seats in service | **14 seats**, the only evidence (2018). With bookings capped at 5 and about 1.8 riders on board on average at 6 pm (T5), capacity should rarely bind | PRESS 2018 | 10 / 7 (smaller or newer vans, spacing rules) | L–M |
| **AS-16** | Party size | Distribution per booking | Mean 1.39 (completed rides); maximum 5 per booking; groups over 5 split | DATA, JHU | Heavier tail | L |
| **AS-17** | Dwell | Boarding and alighting time | 30 s per stop (+ up to 3 min waiting for a late rider) | — | 15 / 30 / 60 s | M |
| **AS-18** | Pickup locations | Curb-to-curb vs stops | Curb-to-curb at the digitized hotspot points | JHU | Consolidated stops (the Penn model) as a policy lever | M |
| **AS-19** | Walk-up riders | Do vans take unbooked riders? | No | JHU booking rules; PEER | — | L |
| **AS-20** | Service area | Exact boundary | The area spanned by the April map points (Homewood + Peabody) | JHU, DATA | — | L |
| **AS-21** | Travel times | Evening road speeds; the router | OSRM free-flow (local, pinned) × a calibrated multiplier | VENDOR (OSM-based), D-12 | Multiplier 1.0–1.5 | M |
| **AS-22** | ETA shown to the rider | Accuracy, and its effect on cancelling | The engine's own estimate; riders react to it | PRESS (complaints about wrong ETAs) | ETA noise | M |
| **AS-23** | Peak definition | When Lyft is allowed | Whenever the trigger in AS-06 fires (all night) | JHU 2026 ("peak service hours") | Fri–Sat only (as in 2018) | M |
| **AS-24** | Bookings by phone | Share of rides and their delay | Same as app bookings | — | +1–2 min booking delay for 10% of requests | L |
| **AS-25** | Hourly chart meaning | Is "hour" the request, pickup or completion hour? | Pickup hour | DATA (unstated) | — | L |

**Decisions this research already challenges** (to be revisited when the scenario definition resumes):
- **D-04** (20/25 limits): those are the East Baltimore goals. Homewood publishes 15/20, and they are soft.
- **D-06** (load anchor of 6.2 completed rides per van-hour): if AS-14 holds, Homewood is nearer 7.7.
- **D-21** (patience): it must explain only about two thirds of "Canceled".
- **D-22** (capacity 4): Hopkins vans were 14 seats in 2018.
- **Player design:** the status quo is a re-planning engine (AS-02), not greedy insertion.

---

## 10. What this means for the project (framing only; the scenario definition is on hold)
1. **The baseline player must be TransLoc-like.**
   - Our planned A (insert and never move) would be a straw man if presented as the status quo.
   - The honest baseline is **T**: event-driven plus a periodic re-plan of all unpicked rides (every 120 s), with a convex wait penalty and the Lyft rule.
   - A (greedy) and C (exact joint MILP) stay as references: below and above the vendor-like heuristic.
2. **The levers worth testing are operating policies, not only algorithms.** Research and data both point to:
   - **the Lyft transfer rule:** threshold, timing, who qualifies. Hopkins controls it directly, and it drives 25% of riders and about a third of cancellations;
   - **the objective weights:** the safety-first order vs ride-time limits, i.e. the long-ride complaints vs waits;
   - **stop consolidation:** Penn's 2026 change cut waits and cancellations;
   - **fleet by hour,** which T1 and T9 already flag.
3. **Coordination still matters,** but the question becomes: *how much do better re-planning and a smarter overflow rule add on top of what TransLoc already does?* That is a sharper and more defensible question than greedy vs MILP.
4. **The calibration targets keep their categories:** completed, canceled (split into rider and Lyft parts in the model), no-show, Lyft share, and wait and ride percentiles.

---

## 11. If we get one chance to ask Hopkins (kept short on purpose)
The team can get only minimal input, so if there is one chance, these three questions retire the most uncertainty:
1. When a ride is moved to Lyft, what triggers it (a wait threshold? the dispatcher's judgement?), and does it show as "Canceled" in TransLoc?
2. How many Homewood vans are in service at 6 pm, and how many seats does each have?
3. Do drivers accept or decline rides in the TransLoc app, or does the system assign them?

---

## 12. Sources (accessed 2 Oct 2026)
**Johns Hopkins**
- JHU Transportation, *Shuttle Services*, including Blue Jay Night Ride, Lyft and East Baltimore (archived 22 Jul 2026): https://jhfre.jhu.edu/ts/transportation/shuttle-services/ (via web.archive.org)
- JHU Transportation, *Night Ride* (archived 19 Apr 2023): https://ts.jhu.edu/Shuttles/Night_Ride/index.html (via web.archive.org)
- Hub, *Blue Jay Shuttle service gets a lift with Lyft partnership*, 26 Jan 2018: https://hub.jhu.edu/2018/01/26/blue-jay-shuttle-lyft-night-ride/
- Hub, *Changes to Blue Jay Shuttle evening routes and Night Ride service*, 22 Aug 2019: https://hub.jhu.edu/announcements/2019/08/22/shuttle-evening-routes-night-ride-changes/
- Hub, *New Blue Jay Shuttle service, East Baltimore*, 11 Jul 2022 (search result): https://hub.jhu.edu/announcements/2022/07/11/new-blue-jay-shuttle-service-east-baltimore

**Press**
- News-Letter, *Lyft partnership expands Blue Jay Shuttle services*, Feb 2018: https://www.jhunewsletter.com/article/2018/02/lyft-partnership-expands-blue-jay-shuttle-services
- News-Letter, *Students critique the changes to the University transportation services*, Sep 2022: https://www.jhunewsletter.com/article/2022/09/students-critique-the-changes-to-the-university-transportation-services
- News-Letter, *N-L survey highlights student opinions on University transportation…*, Oct 2025: https://www.jhunewsletter.com/article/2025/10/n-l-survey-highlights-student-opinions-on-university-transportation-quality-efficiency-and-safety
- News-Letter, *Baltimore transit 101*, Aug 2026: https://www.jhunewsletter.com/article/2026/08/baltimore-transit-101-a-guide-to-going-carless-in-charm-city

**TransLoc (vendor)**
- TransLoc TechLog, *Ridesharing Algorithms in TransLoc OnDemand* (archived 28 Apr 2018): https://techlog.transloc.com/ridesharing-algorithms-in-transloc-ondemand-7acfeddbfe1f (via web.archive.org)
- *TransLoc Drives University Safe Ride Programs to Success*, 15 Dec 2015: https://transloc.com/press/transloc-drives-university-safe-ride-programs-to-success/
- *Demand-response transit is LIVE*, 30 Sep 2015: https://transloc.com/blog/demand-response-transit-live-transloc-ondemand/
- Metro Magazine, *TransLoc unveils new version of OnDemand*, 6 Oct 2015: https://www.metro-magazine.com/news/transloc-unveils-new-version-of-ondemand
- *In Advance Scheduling for TransLoc OnDemand*, 4 May 2016: https://transloc.com/blog/making-life-easier-in-advance-scheduling-for-transloc-ondemand/
- *TransLoc and Uber Partner…*, 2016: https://transloc.com/press/transloc-and-uber-partner-to-pioneer-a-new-standard-in-public-transit/
- *Ford Realigns Mobility Group; Acquiring Autonomic, TransLoc*, 25 Jan 2018: https://transloc.com/press/ford-realigns-mobility-group-acquiring-autonomic-transloc-to-accelerate-growth/
- *TransLoc's New On-Demand Microtransit Model…*, 12 Sep 2018: https://transloc.com/press/translocs-new-on-demand-microtransit-model-sees-broad-adoption-by-transit-agencies-nationwide/
- *Modaxo Welcomes TransLoc*, 1 Mar 2022: https://www.globenewswire.com/news-release/2022/03/01/2394748/0/en/Modaxo-Welcomes-TransLoc.html
- *Solving Dispatcher Challenges Through Technology*, 6 Apr 2022: https://transloc.com/blog/solving-dispatcher-challenges-through-technology/
- *OnDemand Microtransit* product page: https://transloc.com/solutions/on-demand-microtransit/
- *About TransLoc*: https://transloc.com/our-company/
- *Johns Hopkins' Layered Campus Transit Model, Explained*, 2 Sep 2026: https://transloc.com/blog/what-a-student-newspapers-transit-guide-reveals-about-layered-campus-mobility/
- TransLoc OnDemand Driver app, App Store release notes: https://apps.apple.com/us/app/transloc-ondemand-driver/id1049416262
- SIMPO / Rides MTD, *Microtransit Study 2020* (TransLoc simulation section): https://www.greateregypt.org/SIMPO/wp-content/uploads/2021/04/SIMPO-RMTD-microtransit-final-report-2020.pdf

**Company history**
- Eno Center for Transportation, *Bus Tracking Startup Offers Simple Solutions…*, 2 Dec 2016: https://enotrans.org/article/bus-tracking-startup-offers-simple-solutions-riders-transit-agencies/
- NC State Computer Science news (founders): https://www.csc.ncsu.edu/news/288

**Peer programs**
- Columbia, *On-Demand Evening Shuttle* and FAQ: https://transportation.columbia.edu/eveningshuttle ; https://transportation.columbia.edu/content/demand-evening-shuttle-frequently-asked-questions-faqs
- Penn, *Evening Safety Shuttle Ride-Share*: https://transportation.upenn.edu/evening-safety-shuttle-ride-share ; Daily Pennsylvanian, 3 Mar 2026: https://www.thedp.com/article/2026/03/penn-rides-evening-safety-shuttle-new-model-transit
- Northwestern, *Safe Ride FAQs*: https://www.northwestern.edu/nuhelp/safety-and-security/safe-ride/safe-ride-faqs.html
- Duke Today, *Request a Duke Van Ride with TransLoc OnDemand*, 11 Jul 2022: https://today.duke.edu/2022/07/request-duke-van-ride-transloc-ondemand
- Cavalier Daily (UVA), Feb 2025: https://www.cavalierdaily.com/article/2025/02/university-transit-service-makes-efforts-to-enhance-transit-safety
- Pitt, *SafeRider*: https://www.pc.pitt.edu/mobility/shuttle-services/saferider
- Kansas, *SafeRide*: https://transportationservices.ku.edu/saferide
- Old Dominion, *SAFE RIDE*: https://www.odu.edu/transportation-parking-services/transportation/safe-ride
- Rhode Island, *Rhody On-Demand*: https://web.uri.edu/transportation/rhodysaferides/
- South Carolina, *Rides On Demand*: https://sc.edu/about/offices_and_divisions/parking/shuttles/ondemand.php
- NBC Washington, *Georgetown University Partners With Uber for SafeRides Program*: https://www.nbcwashington.com/news/local/georgetown-university-partners-with-uber-for-saferides-program/2073639/
- UC San Diego, *Lyft Concierge* (what the product does): https://blink.ucsd.edu/travel/partners/lyft/concierge.html

**Background (method, cited from the literature, not fetched)**
- Cordeau, J.-F. & Laporte, G. (2007). The dial-a-ride problem: models and algorithms. *Annals of Operations Research* 153, 29–46.
- Jaw, J.-J., Odoni, A., Psaraftis, H. & Wilson, N. (1986). A heuristic algorithm for the multi-vehicle advance request dial-a-ride problem with time windows. *Transportation Research B* 20(3), 243–257.
- Alonso-Mora, J., Samaranayake, S., Wallar, A., Frazzoli, E. & Rus, D. (2017). On-demand high-capacity ride-sharing via dynamic trip-vehicle assignment. *PNAS* 114(3), 462–467.
