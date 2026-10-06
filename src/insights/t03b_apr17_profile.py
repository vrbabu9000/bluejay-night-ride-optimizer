"""T3b: the Apr 17 profile. Where does the outlier night rank on every daily metric?

T3 found Apr 17 (Fri) to be a supply-side outlier. This table ranks it on every daily series
we digitized, so the claim "the system slowed; demand did not spike" can be traced:
ordinary total riders (van + Lyft) and a typical Friday request count, but the fewest van
completions, the most cancellations and Lyft riders, and the longest waits and rides.

Writes outputs/insights/t03b_apr17_profile.csv. Every value is from observations.csv (p07,
p08, p10, p11, p12), so the evidence label is DERIVED (ranks of OBSERVED reads).
"""
import pandas as pd

from common import FIGS, PROCESSED

DAY = "2026-04-17"
obs = pd.read_csv(PROCESSED / "observations.csv")

rows = []
def add(chart, metric, s, unit, note=""):
    s = s.dropna()
    rows.append(dict(chart=chart, metric=metric, value=round(float(s[DAY]), 2), unit=unit,
                     rank_high_to_low=int(s.rank(ascending=False, method="min")[DAY]), n_days=len(s),
                     month_median=round(float(s.median()), 2), note=note))

p07 = obs[obs.chart_id == "p07_status"].pivot_table(index="date_or_hour", columns="metric", values="value")
requests = p07.sum(axis=1)
add("p07", "requests (all statuses)", requests, "requests")
add("p07", "completed rides", p07["completed"], "rides", "fewest of the month")
add("p07", "cancelled", p07["canceled"], "requests")
add("p07", "cancelled share", p07["canceled"] / requests, "share")
fridays = requests[pd.to_datetime(requests.index).dayofweek == 4]
add("p07", "requests, Fridays only", fridays, "requests", "Apr 3, 10, 17, 24")
for cid, metrics, unit in [("p08_passengers", ["passengers"], "van riders"),
                           ("p10_vanlyft_daily", ["total_riders", "van_riders", "lyft_riders"], "riders"),
                           ("p11_wait", ["wait_median", "wait_p90"], "minutes"),
                           ("p12_ride", ["ride_median", "ride_p90"], "minutes")]:
    d = obs[obs.chart_id == cid].pivot_table(index="date_or_hour", columns="metric", values="value")
    for m in metrics:
        add(cid.split("_")[0], m.replace("_", " "), d[m], unit)

out = pd.DataFrame(rows)
out.to_csv(FIGS / "t03b_apr17_profile.csv", index=False)
print(out.to_string(index=False))
