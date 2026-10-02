# parquet-ml \| describe • ingest • log • group • fit • anomaly

[![for-the-badge](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org) [![for-the-badge](https://img.shields.io/badge/PyArrow-FE4F57?style=for-the-badge)](https://arrow.apache.org) [![for-the-badge](https://img.shields.io/badge/pandas-150458?style=for-the-badge)](https://pandas.pydata.org) [![for-the-badge](https://img.shields.io/badge/numpy-013243?style=for-the-badge)](https://numpy.org)

## parquet-ml

Columnar analytics over parquet: describe a schema, ingest JSONL or CSV, group, regress, and flag outliers. Triggered by parquet, dataframe, regression, latency. The implementation is a single file, `scripts/pq.py`. Needs only pyarrow, pandas, and numpy. Use the venv interpreter — the system `python3` lacks those packages.

### Subcommands

| Command | Description |
|---|---|
| `describe FILE.parquet` | Prints the schema plus a per-column profile: nulls, null percent, distinct count, and for numeric columns: min, mean, std, p50, p95, max |
| `ingest FILE.jsonl -o OUT` | Converts JSONL, JSON, or CSV file into typed parquet |
| `log FILE.log -o OUT --grep 'local='` | Parses log lines; lifts `local_ms` from `local=NNms`, `msgs`, model name, `used/window`, `inbound_bytes`/`outbound_bytes` from KiB/MiB suffixes |
| `group FILE.parquet --by kind --agg count,bytes:sum,bytes:max` | Aggregates; spec is `col:agg`; bare name counts that column and rejects nulls |
| `fit FILE.parquet --target ms --features msgs,inbound_bytes` | Ordinary least squares; reports n, degrees of freedom, R², adj R², RMSE, p-value per coefficient, VIF per feature |
| `anomaly FILE.parquet --col local_ms --method mad` | Flags outliers using median absolute deviation; `--method iqr` available; `--threshold` defaults to 3.5 |

### Quick start (3 commands max)

```bash
# Describe a parquet schema
P=/home/toxic/.venv-guidellm/bin/python3
$P scripts/pq.py describe data.parquet

# Ingest JSONL to parquet
$P scripts/pq.py ingest events.jsonl -o events.parquet

# Parse log file to parquet
$P scripts/pq.py log bili.log -o bili.parquet --grep 'local='
```

### Architecture

Single file `scripts/pq.py` applies the parquet convention to any dataset. Every subcommand writes parquet — pass `-o OUT` and the result lands in a parquet file. A description becomes a filtered dataset; the filter becomes a group; the group becomes fit input; nothing is lost to a terminal that scrolled away. `fit` solves normal equations through `np.linalg.lstsq` on the augmented matrix, never through a matrix inverse. p-values use an incomplete-beta continued fraction carried in `pq.py`, validated against published t-table values.

### Config / optional services

- Venv interpreter required: `P=/home/toxic/.venv-guidellm/bin/python3`
- pyarrow, pandas, numpy needed (system `python3` lacks pyarrow)
- `--target <col>` — regression target column for `fit`
- `--features <col1,col2,...>` — feature columns for `fit`
- `--method <iqr|mad>` — anomaly detection method
- `--threshold <n>` — anomaly threshold (defaults to 3.5 for mad, 1.5 for iqr)
- `-o <file>` — output parquet file path

### Dev / contributing

- Place `scripts/pq.py` as the single source file
- Test suite validates p-values against published t-table values
- Add new subcommands by extending the CLI argument parser
- Ensure all output parquet files have descriptive schemas
- Run with venv python: `P=/home/toxic/.venv-guidellm/bin/python3 scripts/pq.py ...`
- New aggregate functions must be validated against existing test suite

### License

Open Claw — see `skill.toml` for details.

### Security

- The venv interpreter is required. The system `python3` has no pyarrow.
- `fit` needs numeric columns. A string column is a type error.
- Reading a 9 MB parquet takes a second or two. Anything wider than a few million rows should be sampled first with `group`.