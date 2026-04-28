#!/usr/bin/env python3
"""
Generate two JSON lookup files from the SVO Filter Profile Service (SVO FPS):

  1. telescope_to_instrument.json
     { telescope: { filter_name: instrument } }

  2. instrument_to_telescope.json
     { instrument: { filter_name: telescope } }

Strategy
--------
The SVO FPS API does not support fetching ALL filters in one call without
a wavelength constraint (it returns 0 rows).  The correct approach is to
sweep the wavelength space in chunks using get_filter_index(), collect every
unique (Facility, Instrument, filterID) triple, then build the two JSONs.

The full optical/near-IR/mid-IR range covered by SVO is roughly
  1 000 Å  →  1 000 000 Å  (100 nm → 100 µm)
We query in steps of CHUNK_AA angstroms and deduplicate on filterID.

Usage
-----
    python generate_svo_filter_jsons.py              # full run
    python generate_svo_filter_jsons.py --demo       # synthetic data, no network
    python generate_svo_filter_jsons.py --out-dir /path/to/data

Requirements
------------
    pip install astroquery astropy
"""

import json
import os
import sys
import time
import argparse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WL_MIN_AA   =      500   # 50 nm  – short end of SVO coverage
WL_MAX_AA   = 1_000_000  # 100 µm – long end of SVO coverage
CHUNK_AA    =   10_000   # 5 µm per chunk  (tune up if slow, down if timeouts)
TIMEOUT_S   =      120   # per-request timeout


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------
DEMO_ROWS = [
    ("Keck/NIRC2.J",        "Keck",    "NIRC2",      "J"),
    ("Keck/NIRC2.H",        "Keck",    "NIRC2",      "H"),
    ("Keck/NIRC2.K",        "Keck",    "NIRC2",      "K"),
    ("HST/ACS_WFC.F606W",   "HST",     "ACS_WFC",    "F606W"),
    ("HST/WFC3_UVIS.F438W", "HST",     "WFC3_UVIS",  "F438W"),
    ("2MASS/2MASS.J",       "2MASS",   "2MASS",       "J"),
    ("2MASS/2MASS.H",       "2MASS",   "2MASS",       "H"),
    ("2MASS/2MASS.Ks",      "2MASS",   "2MASS",       "Ks"),
    ("Spitzer/IRAC.I1",     "Spitzer", "IRAC",        "I1"),
    ("SLOAN/SDSS.r",        "SLOAN",   "SDSS",        "r"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _band_from_filter_id(filter_id: str) -> str | None:
    """
    Extract the band/filter name from an SVO filterID string.

    SVO format:  "Facility/Instrument.Band"
    Examples:
        "Keck/NIRC2.J"        -> "J"
        "2MASS/2MASS.Ks"      -> "Ks"
        "HST/ACS_WFC.F606W"   -> "F606W"
    """
    after_slash = filter_id.split("/", 1)[-1]          # "NIRC2.J"
    band = after_slash.split(".", 1)[-1] if "." in after_slash else after_slash
    return band or None


def _add(mapping: dict, outer_key: str, filter_name: str, inner_val) -> None:
    """
    Insert filter_name -> inner_val into mapping[outer_key].
    Promotes to a sorted list on collision.
    """
    bucket = mapping.setdefault(outer_key, {})
    if filter_name not in bucket:
        bucket[filter_name] = inner_val
        return
    existing = bucket[filter_name]
    if isinstance(existing, list):
        if inner_val not in existing:
            existing.append(inner_val)
            existing.sort(key=lambda x: (x is None, x or ""))
    else:
        if inner_val != existing:
            bucket[filter_name] = sorted(
                [existing, inner_val],
                key=lambda x: (x is None, x or ""),
            )


def _clean(val: str) -> str | None:
    """Return None for blank / placeholder values."""
    v = str(val).strip()
    return None if v in ("", "--", "N/A", "nan") else v


# ---------------------------------------------------------------------------
# Fetch from SVO FPS
# ---------------------------------------------------------------------------
def fetch_all_filters() -> list[dict]:
    """
    Sweep the SVO FPS wavelength space in chunks and collect all unique filters.
    Returns a list of dicts with keys: filter_id, telescope, instrument, filter.
    """
    try:
        from astroquery.svo_fps import SvoFps
        from astropy import units as u
    except ImportError:
        sys.exit(
            "ERROR: astroquery and astropy are required.\n"
            "Install with:  pip install astroquery astropy"
        )

    seen_ids: set[str] = set()
    records:  list[dict] = []

    wl_lo = WL_MIN_AA
    total_chunks = (WL_MAX_AA - WL_MIN_AA + CHUNK_AA - 1) // CHUNK_AA
    chunk_num = 0

    print(
        f"Sweeping SVO FPS from {WL_MIN_AA:,} to {WL_MAX_AA:,} Angstrom "
        f"in {CHUNK_AA:,} Ang chunks ({total_chunks} chunks total) ..."
    )

    while wl_lo < WL_MAX_AA:
        wl_hi = min(wl_lo + CHUNK_AA, WL_MAX_AA)
        chunk_num += 1

        print(f"  [{chunk_num:3d}/{total_chunks}]  {wl_lo:>8,} - {wl_hi:>8,} Ang", end="  ", flush=True)

        try:
            table = SvoFps.get_filter_index(
                wavelength_eff_min=wl_lo * u.angstrom,
                wavelength_eff_max=wl_hi * u.angstrom,
                timeout=TIMEOUT_S,
                cache=False,
            )
        except Exception as exc:
            print(f"WARNING - skipping chunk ({exc})")
            wl_lo = wl_hi
            continue

        new = 0
        for row in table:
            fid = _clean(str(row["filterID"]))
            if not fid or fid in seen_ids:
                continue
            seen_ids.add(fid)

            tel  = _clean(str(row["Facility"]))
            ins  = _clean(str(row["Instrument"]))
            band = _band_from_filter_id(fid)

            records.append(
                {"filter_id": fid, "telescope": tel, "instrument": ins, "filter": band}
            )
            new += 1

        print(f"+{new:4d} new  (total {len(records):,})")
        wl_lo = wl_hi

    print(f"\nFetch complete - {len(records):,} unique filters found.")
    return records


# ---------------------------------------------------------------------------
# Build lookup dicts
# ---------------------------------------------------------------------------
def build_telescope_json(records: list[dict]) -> dict:
    """{ telescope: { filter_name: instrument } }"""
    result: dict = {}
    for r in records:
        tel, flt, ins = r["telescope"], r["filter"], r["instrument"]
        if tel and flt:
            _add(result, tel, flt, ins)
    return result

def build_instrument_json(records: list[dict]) -> dict:
    """{ instrument: { filter_name: telescope } }"""
    result: dict = {}
    for r in records:
        tel, flt, ins = r["telescope"], r["filter"], r["instrument"]
        if ins and flt:
            _add(result, ins, flt, tel)
    return result


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------
def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(path) / 1024
    print(f"  Saved -> {path}  ({len(data):,} top-level keys, {size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Use synthetic data (no network call) - for smoke-testing.",
    )
    parser.add_argument(
        "--outdir", default=".",
        help="Directory to write JSON files into (default: current directory).",
    )
    global CHUNK_AA
    parser.add_argument(
        "--chunk", type=int, default=CHUNK_AA,
        help=f"Wavelength chunk size in Angstroms (default: {CHUNK_AA}). "
             "Increase to speed up, decrease if you get timeouts.",
    )
    args = parser.parse_args()
    CHUNK_AA = args.chunk

    t0 = time.time()

    if args.demo:
        print("DEMO mode - using synthetic data (no network call).")
        records = [
            {"filter_id": fid, "telescope": tel, "instrument": ins, "filter": band}
            for fid, tel, ins, band in DEMO_ROWS
        ]
        print(f"  {len(records)} synthetic records loaded.")
    else:
        records = fetch_all_filters()

    out_tel = os.path.join(args.outdir, "telescope_to_instrument.json")
    out_ins = os.path.join(args.outdir, "instrument_to_telescope.json")

    print("\nBuilding telescope -> instrument lookup ...")
    save_json(build_telescope_json(records), out_tel)

    print("Building instrument -> telescope lookup ...")
    save_json(build_instrument_json(records), out_ins)

    print(f"\nDone in {time.time() - t0:.1f}s")
    print("\nJSON structure:")
    print('  telescope_to_instrument.json : { "Keck":  { "J": "NIRC2", ... } }')
    print('  instrument_to_telescope.json : { "NIRC2": { "J": "Keck",  ... } }')
    print()
    print("Notes:")
    print("  - Filter name = the part after the last '.' in the SVO filterID")
    print("    e.g. 'Keck/NIRC2.J' -> filter name is 'J'")
    print("  - If the same telescope+filter maps to multiple instruments")
    print("    (or vice-versa), the value is a sorted list instead of a string.")


if __name__ == "__main__":
    main()
