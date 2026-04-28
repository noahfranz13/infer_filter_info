import requests
from xml.etree import ElementTree as ET
from typing import List

FACILITIES = [
    "2MASS", "AAO", "ADEOS", "AKARI", "Akatsuki", "AlSat1", "APEX", "APO", "Aqua", "ARCHEOPS",
    "ARGO", "Astrosat", "Beijing1", "Bepi-Colombo", "BICEP", "BLAST", "BOK", "BOOMERANG", "CAHA", "Cameras",
    "Cassini", "CASTOR", "CFHT", "CHEOPS", "Clementine", "CMO-SAI", "COBE", "COMS", "Contour", "Corot",
    "COSMOSOMAS", "CSST", "CSTAR", "CTIO", "Dawn", "DeepImpact", "DENIS", "DOT", "DSCOVR", "Envisat",
    "ERBS", "EROS", "ERS", "ESO", "Euclid", "ExoMars", "FengYun", "Flock", "FLWO", "GAIA",
    "GALEX", "Galileo", "GCOM-C", "GCPD", "Gemini", "Generic", "Geneva", "GeoEye", "Giotto", "GOES",
    "GOTO", "GTC", "Hayabusa2", "HCT", "Herschel", "Himawari", "Hipparcos", "HST", "IAC80", "IKONOS",
    "ING", "INSAT", "InSight", "INT", "Integral", "IRAM", "IRAS", "IRS", "IRSF", "IRTF",
    "ISO", "IUE", "JCMT", "JPSS", "JWST", "Keck", "Kepler", "KOMPSTAT", "KPNO", "Landsat",
    "LasCumbres", "LaSilla", "LBT", "LCO", "LICK", "Liverpool", "LMT", "LRO", "LSST", "LYRA",
    "Mariner10", "Mars2020", "MAXIMA", "McD", "MER", "Mercator", "Messenger", "Meteosat", "METOP", "MEX",
    "Misc", "MKO", "MMT", "MOA", "MOM", "MOST", "MRO", "MSX", "MT", "NAOC",
    "NEAR", "NewHorizons", "NigeriaSat1", "NIMBUS", "NIRT", "NOAA", "NOAO", "NOT", "OAF", "OAJ",
    "OAN-SPM", "OAO", "Odyssey", "OHP", "OLIMPO", "OSIRIS-REX", "OSN", "OVRO", "P200", "Palomar",
    "PAN-STARRS", "Paranal", "Parasol", "Pathfinder", "PLANCK", "Pleiades", "PRIRODA", "QuickBird", "QUIET", "QUIJOTE",
    "RapidEye", "Roman", "Rosetta", "SALT", "SAO", "Scorpio", "SeaStar", "Selene", "Sentinel", "SEOSAT",
    "SkyMapper", "SkySat", "SLOAN", "SMART1", "SOFIA", "SOHO", "SolarOrbiter", "Special", "SPECULOOS", "SPIDER",
    "Spitzer", "SPOT", "SPT", "SSOT", "Stardust", "STELLA", "Subaru", "Swift", "TAUVEX", "TCS",
    "TD1", "Terra", "TESS", "TIROS-N", "TJO", "TNG", "TNO", "TNT", "TopHat", "TRMM",
    "TYCHO", "UK-DMC", "UKIRT", "VATT", "VenusExpress", "Viking", "Voyager", "WASP", "WFIRST", "WHT",
    "WISE", "WIYN", "WMAP", "WorldView", "XMM", "ZiYuan"
]

#!/usr/bin/env python3
"""
Fetch all SVO Filter Profile Service filter IDs for a list of facilities.

For each facility in FACILITIES, queries the SVO FPS for every filter and
collects its filterID (format: "<Telescope>/<Instrument>.<FilterName>").

Output
------
  filter_ids.txt  – one filterID per line
  filter_ids.json – list of filterIDs as a JSON array

Usage
-----
    python get_svo_filter_ids.py
    python get_svo_filter_ids.py --out-dir /path/to/data
    python get_svo_filter_ids.py --demo          # no network, smoke-test

Requirements
------------
    pip install astroquery astropy
"""

import json
import os
import sys
import time
import argparse

DEMO_FILTER_IDS = [
    "Keck/NIRC2.J",
    "Keck/NIRC2.H",
    "Keck/NIRC2.K",
    "HST/ACS_WFC.F606W",
    "HST/WFC3_UVIS.F438W",
    "2MASS/2MASS.J",
    "2MASS/2MASS.H",
    "2MASS/2MASS.Ks",
    "Spitzer/IRAC.I1",
    "SLOAN/SDSS.r",
]


def fetch_filter_ids(facilities: list[str]) -> list[str]:
    """
    Query SVO FPS for each facility and return a deduplicated, sorted list
    of all filterIDs found.
    """
    try:
        from astroquery.svo_fps import SvoFps
    except ImportError:
        sys.exit(
            "ERROR: astroquery is required.\n"
            "Install with:  pip install astroquery astropy"
        )

    all_ids: list[str] = []
    seen: set[str] = set()
    failed: list[str] = []

    pad = max(len(f) for f in facilities)

    for facility in facilities:
        label = facility.ljust(pad)
        print(f"  {label} ...", end="  ", flush=True)
        try:
            table = SvoFps.get_filter_list(facility=facility, cache=False)
        except Exception as exc:
            print(f"FAILED ({exc})")
            failed.append(facility)
            continue

        new_ids = []
        for row in table:
            fid = str(row["filterID"]).strip()
            if fid and fid not in seen:
                seen.add(fid)
                new_ids.append(fid)

        all_ids.extend(new_ids)
        print(f"{len(new_ids):4d} filters  (running total: {len(all_ids):,})")

    if failed:
        print(f"\nWARNING: {len(failed)} facilit(ies) failed to fetch: {failed}")

    all_ids.sort()
    return all_ids


def save_outputs(filter_ids: list[str], out_dir: str) -> None:
    os.makedirs(out_dir, exist_ok=True)

    txt_path  = os.path.join(out_dir, "filter_ids.txt")
    json_path = os.path.join(out_dir, "filter_ids.json")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(filter_ids) + "\n")
    print(f"  Saved -> {txt_path}  ({len(filter_ids):,} entries)")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(filter_ids, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize(json_path) / 1024
    print(f"  Saved -> {json_path}  ({size_kb:.1f} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--out-dir", default=".",
        help="Directory to write output files into (default: current directory).",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Use synthetic data instead of hitting the SVO FPS API.",
    )
    args = parser.parse_args()

    t0 = time.time()

    if args.demo:
        print("DEMO mode – using synthetic data (no network call).")
        filter_ids = sorted(DEMO_FILTER_IDS)
    else:
        print(f"Querying SVO FPS for {len(FACILITIES)} facilities ...\n")
        filter_ids = fetch_filter_ids(FACILITIES)

    print(f"\n{len(filter_ids):,} unique filter IDs collected.")
    print("\nSaving outputs ...")
    save_outputs(filter_ids, args.out_dir)

    print(f"\nDone in {time.time() - t0:.1f}s")
    print("\nOutput files:")
    print("  filter_ids.txt   – one filterID per line")
    print("  filter_ids.json  – JSON array of filterIDs")
    print("\nExample filterID format:  <Telescope>/<Instrument>.<FilterName>")
    print("  e.g.  Keck/NIRC2.J  |  HST/ACS_WFC.F606W  |  2MASS/2MASS.Ks")


if __name__ == "__main__":
    main()
