# GenerateRealData API examples

Runnable examples for the [GenerateRealData](https://generaterealdata.com?ref=github) API: describe the data you need, or send your SQL schema, and get related tables back as CSV, JSON, Excel or SQL.

Field lists can use 232 data types, one of the largest built-in type libraries of any test data generator, 222 of them with their own built-in generator (real airport and ICD-10 codes, VINs and IBANs with valid check digits, real cities with matching postcodes and time zones), and more than 200 automatic links keep related fields in each row consistent. The full list: `GET /api/v1/field-types` or the [API reference](https://generaterealdata.com/docs/api/?ref=github#types).

Every notebook is saved with its output, so you can read the results here without running anything.

## Notebooks

| | Notebook | What it shows | Records used |
|---|---|---|---:|
| 01 | [Quickstart: a dataset from one sentence](notebooks/01_quickstart_from_a_description.ipynb) | Describe the data in plain English, download related tables as CSV | 2,000 |
| 02 | [Test data from your SQL schema](notebooks/02_generate_from_your_sql_schema.ipynb) | Send `CREATE TABLE` statements plus rules; get a SQL script and a SQLite file | 5,000 |
| 03 | [A large dataset: 500,000 rows](notebooks/03_large_dataset_500k_rows.ipynb) | Design on a small run, then scale the same schema up | 502,000 |
| 04 | [Load into PostgreSQL, MySQL, SQL Server or SQLite](notebooks/04_load_into_postgres_mysql_sqlite.ipynb) | One dataset as a script for each database, and how to load it | 12,000 |
| 05 | [The same data every time: seeds for tests and CI](notebooks/05_same_data_every_time_with_seeds.ipynb) | A saved schema plus a seed returns identical data; a `pytest` fixture | 8,000 |
| 06 | [Check the data: foreign keys, totals and dates](notebooks/06_check_the_data_foreign_keys_totals_dates.ipynb) | Reusable SQL checks that prove a dataset is consistent | 5,000 |

To open one in Google Colab, replace `github.com` with `colab.research.google.com/github` in its address.

## Run them yourself

1. **Get an API key.** Sign in at [generaterealdata.com](https://generaterealdata.com?ref=github), open the dashboard and click **Generate API key**. API access is part of the PRO, ULTRA and Enterprise plans.
2. **Keep the key out of the code.** Set it as an environment variable:

   ```bash
   export GRD_API_KEY=grd_live_...          # PowerShell:  $env:GRD_API_KEY = "grd_live_..."
   ```

   In Colab, add it in the **Secrets** panel under the name `GRD_API_KEY`.
3. **Install and open.**

   ```bash
   git clone https://github.com/generaterealdata/api-examples.git
   cd api-examples
   pip install requests pandas notebook
   jupyter notebook notebooks/
   ```

Each generated row uses one record of your plan. None of the examples uses AI-generated fields. Every request can be tried first with `"dry_run": true`, which validates it and reports what it would use without generating anything.

## The shortest example

```python
import os, time, requests

API = "https://generaterealdata.com/api/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['GRD_API_KEY']}"}

ds = requests.post(f"{API}/datasets", headers=HEADERS, timeout=70, json={
    "mode": "prompt",
    "description": "An online shop with customers, products, orders and order items",
    "rows": 2000,
    "format": "csv",
}).json()

while ds["status"] not in ("ready", "failed"):
    time.sleep(5)
    ds = requests.get(f"{API}/datasets/{ds['id']}", headers=HEADERS, timeout=30).json()

with open("shop.zip", "wb") as f:
    f.write(requests.get(f"{API}/datasets/{ds['id']}/download", headers=HEADERS, timeout=300).content)
print(ds["rows_per_table"])
```

## Scripts

The same tasks without a notebook:

| File | What it is |
|---|---|
| [`scripts/python/grd.py`](scripts/python/grd.py) | A command-line tool and an importable `generate()` function: from a prompt, a SQL file or a saved schema; any format; dry runs |
| [`scripts/node/generate.mjs`](scripts/node/generate.mjs) | Node.js 18+, no packages |
| [`scripts/curl/quickstart.sh`](scripts/curl/quickstart.sh) | `curl` and `jq` only |

```bash
python scripts/python/grd.py --sql schemas/shop.sql --notes-file schemas/shop_rules.txt --rows 5000 --format sql --dialect mysql --out shop.sql
```

## Schemas

[`schemas/`](schemas/) holds ready-to-use `CREATE TABLE` files. `shop.sql` (with its rules in `shop_rules.txt`) is the small schema the notebooks use. The others are the schemas of the [free dataset library](https://github.com/generaterealdata/synthetic-datasets): e-commerce, card transactions with fraud labels, SaaS billing, hospital records, smart meters, web analytics, fleet GPS, HR, auto insurance and app users.

## More

- [API reference](https://generaterealdata.com/docs/api/?ref=github): every parameter, error and limit
- [Free synthetic datasets](https://github.com/generaterealdata/synthetic-datasets): 11 ready-made databases with data cards and rule checks
- Questions: support@generaterealdata.com

The code in this repository is released under the [MIT licence](LICENSE).
