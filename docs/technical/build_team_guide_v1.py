from pathlib import Path
import json, html
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/pdf/BlueJay_Team_Technical_Guide.pdf'
NAVY=colors.HexColor('#13324B'); TEAL=colors.HexColor('#087F8C'); LIGHT=colors.HexColor('#EAF3F5'); INK=colors.HexColor('#263746'); GRAY=colors.HexColor('#607080')
S=getSampleStyleSheet()
S.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=29,leading=33,textColor=NAVY,spaceAfter=18))
S.add(ParagraphStyle(name='SubX',fontName='Helvetica',fontSize=13,leading=19,textColor=GRAY,spaceAfter=14))
S.add(ParagraphStyle(name='H1X',fontName='Helvetica-Bold',fontSize=21,leading=26,textColor=NAVY,spaceAfter=14))
S.add(ParagraphStyle(name='H2X',fontName='Helvetica-Bold',fontSize=11.5,leading=15,textColor=TEAL,spaceBefore=10,spaceAfter=5))
S.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=9.5,leading=13.1,textColor=INK,spaceAfter=8))
S.add(ParagraphStyle(name='CellX',fontName='Helvetica',fontSize=8.1,leading=10.6,textColor=INK))
S.add(ParagraphStyle(name='HeadX',fontName='Helvetica-Bold',fontSize=8.4,leading=11.3,textColor=colors.white))
S.add(ParagraphStyle(name='CodeX',fontName='Courier',fontSize=8.1,leading=11,textColor=INK,spaceAfter=8))
flow=[]
def p(x):flow.append(Paragraph(x,S['BodyX']))
def h(x):flow.append(Paragraph(x,S['H2X']))
def title(n,x):
    if flow:flow.append(PageBreak())
    flow.append(Paragraph(f'{n:02d} / TEAM IMPLEMENTATION GUIDE',S['H2X']))
    flow.append(Paragraph(x,S['H1X']))
def table(head,rows,widths):
    data=[[Paragraph(html.escape(str(c)),S['HeadX']) for c in head]]+[[Paragraph(html.escape(str(c)).replace(chr(10),'<br/>').replace(' / ',' /<br/>'),S['CellX']) for c in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('LINEBELOW',(0,0),(-1,0),.5,NAVY)]))
    flow.append(t);flow.append(Spacer(1,9))
def box(x):
    t=Table([[Paragraph(x,S['BodyX'])]],colWidths=[504]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),LIGHT),('BOX',(0,0),(-1,-1),.6,TEAL),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),5)]));flow.append(t);flow.append(Spacer(1,8))
def code(x):flow.append(Preformatted(x,S['CodeX']))

flow.append(Paragraph('BLUE JAY NIGHT RIDE',S['H2X']))
flow.append(Spacer(1,22))
flow.append(Paragraph('A practical guide to<br/>dispatch optimization<br/>with aggregate data',S['TitleX']))
flow.append(Paragraph('Research design, implementation instructions, data contracts and a value-entry workbook for Team FourSight.',S['SubX']))
box('<b>Research question</b><br/>Can coordinating assignments across pending requests serve more passengers within pickup and ride-time limits, using the same fleet?')
p('<b>Version 1.0 | 22 September 2026 | Team discussion and implementation specification</b>')
p('Our only operational source is the April 2026 aggregate report. We will construct several plausible demand scenarios, compare dispatch policies under identical conditions, and identify when coordination helps or hurts. We are not reconstructing individual historical trips.')
h('What this document is - and is not')
p('This is a proposed technical specification. It does not contain newly digitized PDF values, verified service rules, implemented simulation code, or experimental results. Numeric choices described as pilot settings are examples for team review, not Hopkins facts. Existing repository plans that expect future trip records are superseded by the aggregate-only scope here.')
h('How teammates should use it')
p('Read pages 2-3 together. Assign owners on page 12. Enter evidence and values using pages 4-6 and the companion JSON template. Build in the order on page 12, and do not interpret policy results until the verification gates on page 10 pass.')
p('<b>Navigation:</b> 2 Scope and reasoning; 3 experiment; 4 extraction; 5 schemas; 6 parameter register; 7 scenario generation; 8 simulator; 9 optimizer; 10 validation; 11 evaluation; 12 team workflow; 13 configuration and references.')

title(2,'The project in one page')
box('<b>Observed summaries → plausible request streams → one shared simulator → fair policy comparisons → a conditional recommendation.</b>')
h('The operational decision')
p('At each dispatch event, which vehicle should serve each waiting request, and in what pickup/drop-off order? A second decision is whether to wait briefly for additional requests before committing. We will distinguish assignment quality from the effect of waiting.')
h('What counts as success')
p('A useful outcome may be improved service, a rule identifying when coordination is worthwhile, or evidence that a simpler method performs just as well. A positive improvement is not guaranteed. The practical deliverable is a candidate policy and its failure conditions, suitable for consideration in a future operational pilot.')
table(['In scope','Outside the initial scope'],[
('Aggregate audit; broad geographic zones; real road costs','Recovery of actual rider histories or the incumbent policy'),
('Several demand, fleet and travel-time scenarios','A single supposedly correct synthetic history'),
('Pooling-capable baseline and joint assignment','Building-by-building student activity reconstruction'),
('Passenger service, modeled overflow, computational feasibility','Guaranteed Lyft savings, real vehicle control, deployment'),
('Checks on spatial service differences','Demographic fairness claims without demographic evidence')],[252,252])
h('Four evidence labels used throughout')
table(['Label','Meaning and example'],[('OBSERVED','Read from a source with its definition and extraction uncertainty.'),('DERIVED','Computed from compatible observations, e.g. passengers per completed request.'),('ASSUMED','Chosen for a scenario, e.g. campus departures are stronger early.'),('SIMULATED','Produced by the model, e.g. waiting time under policy B.')],[100,404])
p('External geography and road estimates receive their own source and retrieval date. They improve geographic or travel-time realism; they do not establish where students requested trips at a particular hour.')

title(3,'Design the comparison before coding')
table(['Policy','Dispatch trigger','Assignment method'],[('A: immediate greedy','Each request arrival; shared urgent-request rule','Best feasible pickup/drop-off insertion, one request at a time.'),('B: periodic greedy','Every W seconds; shared urgent-request rule','Same insertion rule, processing pending requests oldest first.'),('C: periodic joint','Same W and urgent rule as B','Choose compatible routes for multiple vehicles and requests jointly.')],[105,167,232])
p('<b>B versus A:</b> tests the effect of periodic coordination with a fixed greedy method. <b>C versus B:</b> tests joint assignment at the same window. <b>C versus A:</b> measures the total intervention, but cannot alone explain which component helped.')
h('Pilot settings to review, not operational facts')
p('A small pilot can use W = 30, 60 and 120 seconds, with A as a separate immediate policy. Do not call W = 0 the joint method: it is a different algorithm. Add an event-triggered joint policy later only if meaningful uncommitted decisions remain to optimize.')
h('Rules held fixed across policies')
p('Use the same request stream, vehicle shifts, capacities, road model, starting state, service limits, rejection rules and objective priorities. Freeze the same committed movements. Policies may see current state and previously revealed requests, never future arrivals. Give B and C the same eligibility for reconsidering previously assigned but uncommitted requests.')
h('Urgent-request behavior')
p('At every new request and dispatch tick, calculate remaining pickup slack using a feasible insertion estimate. Requests that cannot safely wait until the next tick invoke a shared immediate greedy fallback. The margin is a named parameter. Count override events; frequent overrides may mean the window is operationally ineffective.')
h('First pilot questions')
p('Does each algorithm create legal pooled routes? Does B add waiting without gains? Does C find better combinations than B? How often does the optimizer fall back or time out? Run contrasting scenarios before scaling experiments.')
box('<b>Gate:</b> agree on the primary metric, dispatch semantics, reconsideration rules and shared emergency fallback before implementing policy C. Otherwise an apparent gain may be a difference in rules.')

title(4,'Extract evidence and reconcile definitions')
p('Create a source manifest first. For each chart, record title, PDF page, reporting period, unit, population/status filter, aggregation grain and anything unknown. Do not rely on numbers quoted in earlier conversations.')
table(['Chart family','Enter into','Checks before downstream use'],[
('Daily requests by status','observations table: total/completed/cancelled/no-show/denied','Are categories exclusive? Are totals given or reconstructed? Can repeat bookings occur?'),
('Hourly completed rides','observations: hour and completed count','Determine whether the hour refers to request, pickup or completion. Unknown remains unknown.'),
('Origin/destination maps','cluster observations and zone allocations','Read counts; assess crop/occlusion and positional uncertainty. Do not assume each marker is a building.'),
('Passengers; van/Lyft summaries','observations with source-system tags','Check trips versus passengers and dates before forming ratios.'),
('Fleet by hour','observations with service coverage','Resolve or scenario-test all-services versus Homewood coverage and reporting days.'),
('Wait/ride summaries','observations with quantile and unit','Check served population and passenger/request weighting. Do not infer a full distribution from a few quantiles.')],[117,164,223])
h('Extraction procedure')
p('1. Calibrate chart axes and units. 2. Read values with intervals where pixels limit precision. 3. Independently re-read selected values, peaks and anomalies. 4. Compare visible tooltip anchors where available. 5. Preserve the original observations when later reconciliation changes interpretation.')
h('Reconciliation ledger')
p('For each proposed identity, record left-hand total, right-hand total, residual, coverage compatibility and action. Examples: daily versus hourly completed totals; passenger series versus van ridership; van plus Lyft versus reported combined total. A discrepancy may be a definition issue, not measurement noise.')
box('<b>Do not force equality:</b> keep an explicit unknown/outside-map component where warranted. Never allocate unexplained residuals to convenient zones just to make the generator balance. If filters remain unknown, model alternative interpretations.')

title(5,'Data contracts and file locations')
p('The following paths are proposed interfaces, not files that already exist. Keep restricted source material and generated operational tables out of public commits according to repository policy. All records need a stable ID and version.')
table(['Proposed path / row unit','Required fields','Who fills it'],[
('data/processed/observations.csv\nOne chart observation','obs_id, chart_id, page, period, date_or_hour, metric, value, lower, upper, unit, population, evidence_status, notes','Data owner: source readings and uncertainty.'),
('data/processed/zones.csv\nOne common geographic zone','zone_id, name, geometry_ref, representative_lat/lon, category, uncertainty_note','Geography owner: approximate zones and sampled routable locations.'),
('data/processed/zone_counts.csv\nZone x endpoint x population','zone_id, endpoint, count, lower, upper, population, allocation_method, source_ids','Data + geography: reconciled mapping with provenance.'),
('data/processed/travel_times.csv\nDirected pair x time band','origin_node, dest_node, time_band, seconds, meters, source, retrieval_date, model_version','Geography owner: road estimates; retain direction.'),
('data/synthetic/requests.parquet\nOne request','request_id, scenario_id, replicate, service_date, arrival_s, origin_node, dest_node, party_size, patience_s','Generator only. No service outcomes here.'),
('outputs/runs/.../request_results.parquet\nOne request x policy run','request_id, run_id, terminal_status, assigned_s, pickup_s, dropoff_s, vehicle_id, wait_s, ride_s, failure_reason','Simulator only; absent outcomes are null, never zero.'),
('outputs/runs/.../run_manifest.json\nOne policy run','run_id, config_hash, scenario_id, seed_set, policy, code_version, solver_settings, input_versions','Runner: supports exact reproduction.')],[161,236,107])
p('Store vehicle schedules separately: vehicle_id, capacity, start_s, end_s, initial_node. Store event logs separately: event_id, simulation_time, event_type, vehicle_id, request_id, location and load. The event log is essential for debugging impossible results.')
p('<b>Time convention:</b> seconds since the chosen service-night start internally; America/New_York and ISO dates in metadata. Define after-midnight attribution explicitly. Never mix minutes and seconds in model inputs.')

title(6,'Parameter register: where values go')
p('Fill the companion <b>team_config.template.json</b>, then save an experiment-specific copy. A null value means unresolved, not zero. Numerical choices need a source or an assumption rationale in the decision log. Every required null must be resolved before a main run.')
table(['Config key','Unit / value to enter','Basis and owner'],[
('service.start_local / end_local','Local HH:MM; initially null','Data owner checks report coverage and defines service night.'),
('service.wait_limit_s / ride_limit_s','Seconds; initially null','Team verifies applicable rules. Earlier 20/25 minute discussion is provisional.'),
('fleet.schedule_path','Path to vehicle-level schedule; null','Simulation owner defines plausible fleet scenarios. Do not silently use all-services counts.'),
('demand.daily_totals_path','Path to extracted daily totals; null','Data owner specifies request population and repeat-booking caveat.'),
('demand.hourly_request_weights','Nonnegative vector summing to 1; null','Model owner supplies alternative assumptions; not copied as fact from hourly completions.'),
('demand.party_size_probs','Discrete probabilities; null','Use compatible passenger/request ratio if available; a mean alone does not identify probabilities.'),
('demand.patience_spec','Distribution, parameters, limits; null','Scenario assumption. Independent of policy for paired runs.'),
('spatial.beta_per_min / scenario_path','Distance sensitivity; scenario table; null','Model owner varies gravity and time-direction assumptions.'),
('travel.matrix_path / multiplier','Path; positive factor; null','Geography owner supplies road model and congestion cases.'),
('simulation.pickup_dwell_s / dropoff_dwell_s','Seconds; null','Simulation owner: assumptions. Vehicle hold limit is not automatically average dwell.'),
('dispatch.windows_s / urgent_margin_s','[30,60,120] pilot / null','Team selects windows and shared urgency margin.'),
('solver.time_limit_s / max_new_per_route','Seconds / integer; null','Optimization owner sets based on benchmark runtime.'),
('evaluation.replicates / seed_base','Positive integer / integer; null','Analysis owner sets after pilot variability and seed design.')],[173,170,161])
p('<b>Also decide:</b> travel-time randomness, allowable reassignment, overflow trigger, shift-end rule, horizon clearing, scenario weights, service guardrails and primary comparison. Record these before experiments; do not bury them in code.')

title(7,'Construct the demand scenarios')
h('Step 1 - reconcile spatial evidence')
p('Place origins and destinations on a common coarse zone system. Broad and close-up maps may overlap; do not double-count them. Use uncertain allocations when cluster footprints are not known. A map count is not proof of its exact spatial extent or population.')
h('Step 2 - create candidate O-D-time weights')
p('For origin o, destination d and hour h, use a positive seed such as:')
code('seed[o,d,h] = base[o,d] * exp(-beta * travel_min[o,d,h])\n                * activity_weight[o,d,h]')
p('The activity weight represents an explicitly chosen directional scenario. Compare early campus departures, early campus arrivals and mixed flows. Include feasible intra-zone trips where relevant; coarse zones can contain legitimate journeys. Exclude impossible pairs with documented structural zeros, not merely inconvenient ones.')
h('Step 3 - balance compatible margins')
p('For compatible populations, use iterative scaling to match origin totals, destination totals and the selected hourly distribution. Stop when residuals meet a declared tolerance. An average-zero directional adjustment alone does not guarantee these margins. Infeasible support must produce a diagnostic, not silent redistribution.')
p('If maps describe completed trips, their margins constrain baseline served outputs, not automatically all generated requests. Either evaluate both population interpretations or use the maps as an explicit approximate spatial prior and report baseline mismatch. Label which interpretation each scenario uses.')
h('Step 4 - sample request streams')
p('Choose a daily request count from compatible observations or an explicitly scaled scenario. Allocate requests to hours using assumed arrival shares, then draw timestamps under smooth or bursty alternatives. Sample O-D pairs, routable endpoints, party sizes and patience. Use separate reproducible random streams for each component.')
h('Step 5 - distinguish population targets from sample variation')
p('A probability table can match target margins while a sampled night differs by chance. For exact synthetic monthly margins, use constrained integer allocation; otherwise report sampling residuals. Do not require every night to reproduce a monthly spatial pattern exactly.')
box('<b>Keep input and outcome apart:</b> observed wait and pooled ride-duration summaries are baseline checks. They are not independent request attributes to draw and then reuse as simulated service results. Road time is not pooled ride time.')

title(8,'Simulator behavior and accounting')
h('Event loop')
code('advance vehicles to next event time\napply arrivals, shift changes, pickups and dropoffs\nupdate pending requests and remaining route feasibility\ninvoke dispatch if arrival/tick/urgency rules require it\ncommit allowed decisions and schedule next events\nlog state transitions; repeat until the night clears')
p('Specify deterministic ordering for simultaneous events. For example, process drop-offs before pickups, then new requests, then patience/deadline checks and dispatch, with explicit equality rules. Use the same ordering for every policy.')
h('Request states')
p('An active request may be pending, assigned or onboard. Each request ultimately has exactly one terminal status: <b>completed, abandoned, modeled overflow, or unserved at close</b>. State changes require a reason code. An assigned rider can abandon before pickup if that is the shared patience rule; onboard riders cannot simply disappear.')
h('Outcome definitions')
p('<b>Modeled overflow:</b> an explicit outside-option decision under the chosen fallback rule. A request being infeasible at one instant is not necessarily proof it cannot be served later. Specify whether it remains pending until a deadline, is handed off immediately, or uses a forecast threshold.')
p('<b>Abandonment:</b> a rider leaves before pickup according to the scenario patience model. This is not automatically identical to reported cancellations. Administrative cancellations, duplicates and no-shows may not be represented; document that gap.')
h('Vehicle commitments and end of service')
p('Freeze travel already underway and protect all onboard passengers. Define whether the next stop is frozen or only the current road movement. At shift end, stop assigning new work according to the shared rule and complete accepted service. Continue simulation beyond the last arrival long enough to clear accepted trips; account for residual requests explicitly.')
h('Constraints checked after every route change')
p('Pickup precedes drop-off; each party stays on one vehicle; load remains between zero and capacity; all travel has a valid directed cost; service windows and existing commitments remain feasible. Distinguish projected feasibility at assignment from actual attainment if travel times are stochastic.')
box('<b>Accounting identity:</b> generated requests = completed + abandoned + modeled overflow + unserved at close. Check passenger-weighted totals separately. No request may appear in two terminal categories.')

title(9,'A pooling-capable joint optimizer')
p('A practical first MILP can select from precomputed feasible route options. Each option is an ordered sequence of pickups and drop-offs for one vehicle, retaining its required stops and adding one or more pending requests. Feasibility is checked by simulating that sequence from the current state.')
h('Notation and model')
p('Let R(v) be the candidate routes for vehicle v. Let x[v,r] be a binary route-selection variable. Let a[q,v,r] indicate whether route r serves pending request q. Let y[q] indicate that q is selected for service now, and p[q] be its party size.')
code('sum_r x[v,r] = 1                         for each vehicle v\nsum_v,r a[q,v,r] * x[v,r] = y[q]          for each request q\nx[v,r], y[q] in {0,1}\n\nPriority 1: maximize sum_q p[q] * y[q]\nPriority 2: minimize added waiting, then added travel\n            while preserving the best Priority 1 value')
p('Include a no-new-request route for every vehicle. Existing commitments must be served in every eligible option or fixed explicitly. Unselected requests remain pending unless the common overflow or abandonment rule fires. The myopic objective supports the experiment but does not guarantee maximum service over the entire night.')
h('Construct route options carefully')
p('Enumerate feasible insertions and small combinations of new requests, using a configurable cap and pruning. Include options with multiple new requests on the same vehicle; otherwise the experiment cannot test joint pooling. Record the candidate-generation limits and route counts. Where possible, include the greedy solution as a candidate incumbent.')
h('Objective and fairness controls')
p('Use the same service-first priorities and stable tie-breaking for greedy insertion. If passenger weighting disadvantages single riders, report request-level service rates and consider a separate sensitivity case. Do not change objective weights after seeing which policy wins without marking the analysis exploratory.')
h('Computation is part of the policy')
p('Record solve time, incumbent quality and timeouts. Specify whether computational delay enters simulated time; an idealized zero-delay model must be labeled. A time-limited feasible incumbent may be used; otherwise invoke the documented greedy fallback. Bounds apply only to the restricted candidate model, not to the entire routing problem.')
box('<b>Prototype warning:</b> ordinary request-to-vehicle Hungarian matching selects at most one new request per vehicle per round. It is not equivalent to this route-combination model.')

title(10,'Verification, calibration and release gates')
table(['Gate','Required evidence','If it fails'],[
('G1: input integrity','Definitions and coverage recorded; reconciliation residuals explained or retained; units verified.','Do not combine incompatible series. Carry alternative interpretations.'),
('G2: simulator correctness','Hand-solvable cases: one request; compatible pooling; capacity conflict; urgent deadline; unreachable pair; shift end; abandonment.','Fix engine and accounting before comparing policies.'),
('G3: policy parity','Same inputs, commitments, eligibility, service rules and information; matched B/C windows.','Treat comparisons as invalid until aligned.'),
('G4: baseline plausibility','Compare compatible completion and hourly patterns plus wait/ride summaries, with source uncertainty.','Diagnose model/population mismatch; narrow claims.'),
('G5: experimental reliability','Paired repetitions; uncertainty intervals; runtime logs; scenario sensitivity.','Increase justified repetitions or report uncertainty.'),
('G6: recommendation','Fresh test runs for any selected rule; harms and failure conditions reported.','Present exploratory findings rather than a deployment recommendation.')],[104,227,173])
h('Calibration protocol')
p('Before fitting, list which summaries are calibration targets and which are held-out checks. Fit or choose only a small, declared parameter set. Retain multiple plausible parameter combinations if the data cannot distinguish them. Freeze them before policy comparisons. Apply each retained configuration to every policy.')
h('Limits of held-out checks')
p('With one month and shared aggregates, held-out summaries are not fully independent evidence. Passing them makes the model more plausible but does not establish true demand, the real dispatch policy or expected real-world savings. A baseline mismatch may be tolerable for a method experiment, but it limits Hopkins-specific interpretation.')
h('Do not validate by construction')
p('Reproducing margins enforced by balancing is an integrity check. It is not behavioral validation. Matching calibrated waiting summaries is not a prediction. A different dispatch policy should be allowed to change completion, waiting and overflow outcomes; never force those historical outcomes on every policy.')

title(11,'Metrics, uncertainty and interpretation')
table(['Metric','Definition and reporting rule'],[
('Primary: timely passengers served','Sum party sizes for completed requests satisfying both wait and ride limits. Report count and share of all requested passengers.'),
('Request service rate','Completed requests / all generated requests. Also report timely completed requests / all requests.'),
('Waiting and riding','Wait = pickup - arrival; ride = dropoff - pickup. Report quantiles among served riders with weighting stated. Pair with unserved metrics to expose selection effects.'),
('Modeled overflow / abandonment','Separate counts and rates with all requests as denominator. Never automatically label these Lyft trips or real cancellations.'),
('Service by area','Origin/destination-zone service rates, waits and sample sizes. Avoid conclusions from tiny groups.'),
('Vehicle and solver performance','Occupied, empty and idle time; end-of-shift overtime; runtime percentiles, feasible-solution and fallback rates.')],[149,355])
h('Paired comparisons')
p('For each scenario and replicate, reuse the same request stream and exogenous environment across policies. Pre-generate randomness by request ID and time/location where appropriate; one shared seed is insufficient if policies consume random draws in different orders. Compute policy differences within each paired night.')
p('Report mean differences and uncertainty intervals across independent replicate pairs within a scenario. Use a paired bootstrap or a justified alternative. Choose replication count from pilot variability and a team-defined practical effect size. Simulation intervals represent random variation within assumptions, not all model uncertainty.')
h('Guardrails and policy selection')
p('Enter the minimum meaningful gain and maximum acceptable service deterioration before the main experiment. If limits are hard in a deterministic model, compliant served trips should satisfy them by construction; emphasize service coverage and wait distributions too. Without justified scenario probabilities, show scenario-specific results rather than an arbitrary weighted average.')
h('Final figures')
p('Produce an aggregate audit plot, scenario map, wait-versus-service tradeoff, policy-by-scenario improvement table and runtime summary. Show losses and null results. Separate random variation from differences across fleet, timing, patience and travel assumptions.')
box('<b>Permitted conclusion:</b> "Policy C improved timely service in these tested scenarios, under these assumptions."<br/><b>Unsupported conclusion:</b> "Hopkins will save this percentage of Lyft trips."')

title(12,'Team workflow and decision worksheet')
table(['Work package / suggested owner','Deliverable','Completion gate'],[
('1. Data steward\nName: __________________','Observation tables, dictionary, reconciliation ledger; aggregate diagnostics in parallel.','G1 passes or unresolved items have explicit downstream scenarios.'),
('2. Geography + demand\nName: __________________','Zones, road matrix, scenario generator and assumptions.','Reproducible streams; feasible geography; margins and population interpretation documented.'),
('3. Simulation engineer\nName: __________________','Event engine, accounting, greedy policies, logs.','G2 and G3 pass on hand-checkable cases.'),
('4. Optimization + evaluation\nName: __________________','Candidate-route optimizer, pilot experiments, sensitivity and paired analysis.','G4-G6 assessed; all limitations reported.')],[172,186,146])
p('Roles can be shared, but each artifact needs one accountable owner and a different reviewer. Work packages 1 and 2 can progress together after the source manifest; optimization can use tiny artificial instances while the demand model is being built.')
h('Suggested notebooks - interfaces to later implementation')
code('00_source_audit.ipynb          observations + reconciliation\n01_aggregate_diagnostics.ipynb profiles + anomalies\n02_zones_and_travel.ipynb      geography + directed costs\n03_scenario_generator.ipynb    demand + construction checks\n04_simulator_checks.ipynb      invariant and example checks\n05_policy_pilot.ipynb          timing + assignment contrasts\n06_main_experiments.ipynb      paired runs + metrics\n07_sensitivity_and_report.ipynb assumptions + recommendation')
h('First team meeting: decisions to fill in')
p('<b>Primary comparison:</b> __________________  <b>Owner:</b> __________________<br/><b>Service rules source:</b> __________________  <b>Reviewer:</b> _______________<br/><b>Initial geographic extent:</b> ________________________________________<br/><b>Required pilot scenarios:</b> ________________________________________<br/><b>Practical improvement / harm thresholds:</b> __________________________<br/><b>Pilot review date:</b> ______________  <b>Main run freeze date:</b> ____________')
p('Use gates rather than an assumed semester calendar. If behind, cut fine spatial detail, optional place enrichment and extra policy windows first. Keep correct pooling, fair comparisons, burst sensitivity where relevant, accounting checks and honest uncertainty reporting.')

title(13,'Configuration, decisions and references')
h('How to enter values')
p('The companion template is <b>docs/technical/team_config.template.json</b>. Copy it to a named experiment configuration before filling it. JSON has no comments, so rationale belongs in a separate decision log. Paths in the template are proposed interfaces; input datasets still need to be produced.')
code('Example decision-log record (illustrative only):\nparameter: dispatch.urgent_margin_s\nvalue: 30\nevidence_status: ASSUMED\nreason: pilot buffer before the next dispatch opportunity\nalternatives: [0, 30, 60]\nowner: TEAM_MEMBER\nreviewer: TEAM_MEMBER\ndecision_date: YYYY-MM-DD\nstatus: proposed')
p('The value 30 above is an example of documentation, not a recommended safety margin. For observations, replace the rationale with a source page and extraction interval. For verified rules, record the official source and applicable date. Required unresolved values must cause configuration validation to fail.')
h('Before launching a main experiment')
p('Confirm that required fields are populated; probabilities sum to one; units and date conventions match; input paths and versions exist; every scenario has a rationale; baseline checks are recorded; policy objectives are fixed; random streams are paired; solver fallback works; output directories are unique; and the code/config/input versions are saved.')
h('Sources and scope of verification')
p('<b>Operational source to extract:</b> <i>HW Night Ride Data April 2026.pdf</i>, provided in the repository. This guide specifies an extraction workflow; it does not independently certify chart values or service targets.')
p('<b>Project context reviewed:</b> repository README.md and the project-direction discussion through 22 September 2026. The README still describes potential trip-level acquisition; this guide adopts the user-confirmed constraint that no additional operational data will arrive.')
p('<b>Methods:</b> the route-selection formulation, experimental controls and proposed schemas in this guide are a design specification. They are not a literature review or a claim of methodological novelty. Add primary research and verified tool documentation during implementation, before making publication or provider-capability claims.')
p('<b>Research disclosure:</b> this guide was drafted with AI assistance. Team members should verify source readings, understand and review the model, and document AI use according to the course requirements. The deliverable has no simulated performance findings yet.')
box('<b>Next concrete milestone:</b> a reviewed source manifest, a filled pilot configuration and one hand-verified pooled-route example. Once those exist, the team can build with a shared understanding of what is measured and what is assumed.')

class NumberedCanvas(canvas.Canvas):
    def __init__(self,*a,**k):super().__init__(*a,**k);self.states=[]
    def showPage(self):self.states.append(dict(self.__dict__));self._startPage()
    def save(self):
        total=len(self.states)
        for st in self.states:
            self.__dict__.update(st)
            self.setStrokeColor(TEAL);self.setLineWidth(1.2);self.line(54,754,558,754)
            self.setFont('Helvetica',8);self.setFillColor(GRAY)
            self.drawString(54,766,'BLUE JAY NIGHT RIDE  /  TECHNICAL GUIDE  /  v1.0')
            self.line(54,43,558,43);self.drawString(54,29,'Team FourSight | Proposed specification | 22 September 2026')
            self.drawRightString(558,29,f'{self._pageNumber} / {total}')
            super().showPage()
        super().save()
OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=(612,792),rightMargin=54,leftMargin=54,topMargin=54,bottomMargin=58,title='Blue Jay Night Ride - Team Technical Guide',author='Team FourSight | AI-assisted draft')
doc.build(flow,canvasmaker=NumberedCanvas)
config={
'metadata':{'status':'TEMPLATE_NOT_RUNNABLE','version':'1.0','timezone':'America/New_York','decision_log_path':None},
'service':{'start_local':None,'end_local':None,'after_midnight_date_rule':None,'wait_limit_s':None,'ride_limit_s':None,'rules_source':None},
'fleet':{'schedule_path':None,'shift_end_rule':None},
'demand':{'daily_totals_path':None,'hourly_request_weights':None,'party_size_probs':None,'patience_spec':None,'arrival_model':None,'map_population_interpretation':None},
'spatial':{'zones_path':None,'zone_counts_path':None,'beta_per_min':None,'scenario_path':None,'balance_tolerance':None,'unknown_mass_rule':None},
 'travel':{'matrix_path':None,'multiplier':None,'stochastic_spec':None},
'simulation':{'pickup_dwell_s':None,'dropoff_dwell_s':None,'simultaneous_event_order':None,'commitment_rule':None,'reassignment_rule':None,'overflow_rule':None,'end_of_night_rule':None},
'dispatch':{'policies':['immediate_greedy','periodic_greedy','periodic_joint'],'windows_s':[30,60,120],'windows_status':'ILLUSTRATIVE_PILOT_CHOICES','urgent_margin_s':None,'fallback':'shared_immediate_greedy','objective':'service_first_then_added_wait_then_travel'},
'solver':{'time_limit_s':None,'max_new_per_route':None,'delay_accounting_rule':None},
'evaluation':{'replicates':None,'seed_base':None,'random_stream_scheme':None,'primary_comparison':None,'minimum_meaningful_gain':None,'maximum_acceptable_harm':None,'calibration_targets':None,'held_out_checks':None,'scenario_weights':None}
}
(ROOT/'docs/technical/team_config.template.json').write_text(json.dumps(config,indent=2)+'\n')
print(OUT)
