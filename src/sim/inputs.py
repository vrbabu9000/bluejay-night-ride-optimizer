"""Frozen scenario inputs and the travel table (read-only).

Nothing here writes to data/. The content hash of a scenario is recomputed from the raw file bytes exactly as
generator_v2.write_scenario computed it, and compared with FROZEN_v2.json before any run.

Units: integer seconds from 18:00; travel legs are Python round() of the float product t0 x m (the same rule as
generator_v2.T(), so the answer keys reproduce), applied once per leg (D-47). Distances are matrix metres.
"""
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SCEN = ROOT / "data" / "scenarios" / "v2"
MATRIX = ROOT / "data" / "processed" / "tt_locations_v2.csv"


@dataclass(frozen=True)
class Request:
    """Public part of a request: what a dispatcher may see once the request has arrived."""
    rid: str
    t: int          # request time, s
    o: str
    d: str
    q: int          # party size
    direct_s: int   # unscaled t0(o, d), for reporting


@dataclass(frozen=True)
class Hidden:
    """Hidden per-request traits. Only the engine holds these."""
    patience_s: int
    noshow_u: float
    consent_u: float
    lyft_delay_s: int


@dataclass(frozen=True)
class Van:
    vid: str
    start_loc: str
    capacity: int
    avail_start_s: int
    avail_end_s: int


class Travel:
    """Travel oracle over the v2 matrix. Van legs use m_v, Lyft rides use m_L, each applied once."""

    def __init__(self, m_v=1.0, m_L=1.0, path=MATRIX):
        tt = pd.read_csv(path, usecols=["origin", "dest", "seconds", "meters"])
        self._sec = dict(zip(zip(tt.origin, tt.dest), tt.seconds))
        self._dm = {k: int(round(v * 10)) for k, v in zip(zip(tt.origin, tt.dest), tt.meters)}   # decimetres, exact
        self.m_v, self.m_L = m_v, m_L
        self.matrix_sha256 = hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def t0(self, a, b):
        return self._sec[(a, b)]

    def van(self, a, b):
        return int(round(self._sec[(a, b)] * self.m_v))

    def lyft(self, a, b):
        return int(round(self._sec[(a, b)] * self.m_L))

    def dm(self, a, b):
        """Distance in decimetres (integer; the matrix has one decimal of metres)."""
        return self._dm[(a, b)]


def content_hash(folder):
    folder = Path(folder)
    blobs = [(folder / n).read_bytes() for n in ("requests.csv", "latent.csv", "availability.csv")]
    params = json.loads((folder / "scenario.json").read_text())["params"]
    canon = json.dumps(params, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(b"".join(blobs) + canon).hexdigest()


def frozen_hashes():
    return json.loads((SCEN / "FROZEN_v2.json").read_text())


@dataclass
class Scenario:
    name: str
    folder: Path
    params: dict
    requests: list
    hidden: dict
    vans: list
    content_hash: str


def load(name, check_hash=True):
    """Load a frozen v2 scenario, e.g. 'L1' or 'L5/r00'. Raises if its content hash differs from FROZEN_v2.json."""
    folder = SCEN / name
    h = content_hash(folder)
    if check_hash and frozen_hashes().get(name) != h:
        raise RuntimeError(f"{name}: content hash {h[:12]} does not match FROZEN_v2.json")
    params = json.loads((folder / "scenario.json").read_text())["params"]
    rq = pd.read_csv(folder / "requests.csv")
    lt = pd.read_csv(folder / "latent.csv").set_index("request_id")
    av = pd.read_csv(folder / "availability.csv")
    requests = [Request(r.request_id, int(r.t_request_s), r.o_loc, r.d_loc, int(r.party), int(r.direct_s))
                for r in rq.itertuples()]
    hidden = {rid: Hidden(int(x.patience_s), float(x.noshow_u), float(x.consent_u), int(x.lyft_delay_s))
              for rid, x in lt.iterrows()}
    vans = [Van(v.van_id, v.start_loc, int(v.capacity), int(v.avail_start_s), int(v.avail_end_s))
            for v in av.itertuples()]
    return Scenario(name, folder, params, requests, hidden, vans, h)
