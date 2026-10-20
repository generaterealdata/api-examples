"""Generate a dataset from the command line, or import generate() in your own code.

    export GRD_API_KEY=grd_live_...        (PowerShell:  $env:GRD_API_KEY = "grd_live_...")

    python grd.py --prompt "A gym with members, classes and bookings" --rows 2000 --format csv --out gym.zip
    python grd.py --sql ../../schemas/shop.sql --notes-file ../../schemas/shop_rules.txt --rows 5000 --format sql --dialect mysql --out shop.sql
    python grd.py --schema-id sch_xxxxxxxx --rows 5000 --seed 42 --format json --out data.json
    python grd.py --sql ../../schemas/shop.sql --rows 500000 --dry-run

Needs Python 3.8+ and the requests package. API reference: https://generaterealdata.com/docs/api/
"""
import argparse
import os
import sys
import time
import uuid
from pathlib import Path

import requests

API = "https://generaterealdata.com/api/v1"


class ApiError(RuntimeError):
    pass


def _call(method, path, key, **kwargs):
    """One request. Waits and retries when rate-limited or while another dataset is still running."""
    headers = {"Authorization": f"Bearer {key}", **kwargs.pop("headers", {})}
    while True:
        r = requests.request(method, API + path, headers=headers, timeout=90, **kwargs)
        data = r.json()
        code = data.get("error", {}).get("code") if isinstance(data, dict) else None
        if r.status_code == 429 or code == "run_in_progress":
            time.sleep(int(r.headers.get("Retry-After", 15)))
            continue
        if r.status_code >= 400:
            e = data["error"]
            raise ApiError(f"{e['code']}: {e['message']}" + (f" Hint: {e['hint']}" if e.get("hint") else ""))
        return data


def generate(spec, out_path=None, key=None, quiet=False):
    """
    Starts a dataset, waits for it and (if out_path is given) saves the file. Returns the final status.
    spec is the request body, e.g. {"mode": "prompt", "description": "...", "rows": 2000, "format": "csv"}.
    For format "sql", a SQLite copy is saved next to the script as <name>.sqlite.
    """
    key = key or os.environ["GRD_API_KEY"]
    # The Idempotency-Key makes it safe to send the same request again if the connection drops.
    ds = _call("POST", "/datasets", key, json=spec, headers={"Idempotency-Key": str(uuid.uuid4())})
    if spec.get("dry_run"):
        return ds
    while ds["status"] not in ("ready", "failed"):
        if not quiet:
            print(f"  {ds['status']}...", file=sys.stderr)
        time.sleep(5)
        ds = _call("GET", f"/datasets/{ds['id']}", key)
    if ds["status"] == "failed":
        raise ApiError(f"{ds['error']['code']}: {ds['error']['message']}")
    if out_path:
        out_path = Path(out_path)
        targets = [(None, out_path)] + ([("db", out_path.with_suffix(".sqlite"))] if spec.get("format") == "sql" else [])
        for file, path in targets:
            with requests.get(f"{API}/datasets/{ds['id']}/download", params={"file": file} if file else None,
                              headers={"Authorization": f"Bearer {key}"}, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if not quiet:
                print(f"  saved {path}", file=sys.stderr)
    return ds


def main():
    p = argparse.ArgumentParser(description="Generate a synthetic dataset with the GenerateRealData API.")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--prompt", help="describe the data in plain English")
    source.add_argument("--sql", help="path to a file with CREATE TABLE statements")
    source.add_argument("--schema-id", help="reuse a saved schema (sch_...)")
    p.add_argument("--notes", help="extra rules in plain English")
    p.add_argument("--notes-file", help="read the extra rules from a file")
    p.add_argument("--rows", type=int, required=True, help="total rows across all tables (1 to 500,000)")
    p.add_argument("--format", choices=["json", "csv", "excel", "sql"], default="csv")
    p.add_argument("--dialect", choices=["postgresql", "mysql", "sqlserver", "sqlite"], help="for --format sql")
    p.add_argument("--seed", type=int, help="same seed and schema give the same data")
    p.add_argument("--use-ai", action="store_true", help="with --prompt: let free-text fields be written by AI (uses AI-generated fields)")
    p.add_argument("--dry-run", action="store_true", help="validate and show what it would use; generate nothing")
    p.add_argument("--out", help="where to save the file")
    a = p.parse_args()
    if not os.environ.get("GRD_API_KEY"):
        sys.exit("Set the GRD_API_KEY environment variable to your API key first.")
    if not a.dry_run and not a.out:
        sys.exit("Give --out to save the file, or --dry-run to only check the request.")

    spec = {"rows": a.rows, "format": a.format}
    notes = Path(a.notes_file).read_text(encoding="utf-8").strip() if a.notes_file else a.notes
    if a.prompt:
        spec.update(mode="prompt", description=a.prompt, use_ai=a.use_ai)
    elif a.sql:
        spec.update(mode="sql", sql=Path(a.sql).read_text(encoding="utf-8"))
    else:
        spec.update(mode="schema", schema_id=a.schema_id)
    if notes and not a.schema_id:
        spec["notes"] = notes
    if a.dialect:
        spec["dialect"] = a.dialect
    if a.seed is not None:
        spec["seed"] = a.seed
    if a.dry_run:
        spec["dry_run"] = True

    try:
        ds = generate(spec, a.out)
    except ApiError as e:
        sys.exit(str(e))
    if a.dry_run:
        print(f"Valid. Records needed: {ds['credits_required']:,} (available: {ds['credits_available']:,}).")
    else:
        print(f"{ds['rows_generated']:,} rows: {ds['rows_per_table']}")
        print(f"schema_id {ds['schema_id']}, seed {ds['seed']} (send both to get the same data again)")


if __name__ == "__main__":
    main()
