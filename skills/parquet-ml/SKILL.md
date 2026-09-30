---
name: parquet-ml
description: >
  Columnar analytics over parquet: describe a schema, ingest JSONL or CSV, group,
  regress, and flag outliers. Triggered by parquet, dataframe, regression, latency.
---

## Concept

Parquet is the tree's existing convention for anything that grows past a few
hundred rows. `forensics-srv/server.py` and `src/todo_loop.py` already use it.
This skill is the same idea applied to *any* dataset instead of a fixed one.

The implementation is a single file, `scripts/pq.py`.

It needs only pyarrow, pandas, and numpy.

Use the venv interpreter. The system `python3` lacks those packages.

```
P=/home/toxic/.venv-guidellm/bin/python3
$P scripts/pq.py describe FILE.parquet
```

## When to use this

Reach for it when the data is a file and the question is quantitative.

Which rows are slow? Which group dominates a total? Does one feature explain
a latency? Which values are outliers?

Reach for `grep` instead when the question is whether a *string* appears.

## The six subcommands

```
pq.py describe  FILE.parquet
pq.py ingest    events.jsonl -o events.parquet
pq.py log       bili.log -o bili.parquet --grep 'local='
pq.py group     FILE.parquet --by kind --agg count,bytes:sum,bytes:max
pq.py fit       FILE.parquet --target ms --features msgs,inbound_bytes
pq.py anomaly   FILE.parquet --col ms --method mad
```

**describe** prints the schema plus a per-column profile: nulls, null percent,
distinct count, and for numeric columns min, mean, std, p50, p95, and max.

**ingest** converts a JSONL, JSON, or CSV file into typed parquet.

**log** parses a log line of the form `TIMESTAMP [level] [tag] message`. It
lifts `local_ms` from `local=NNms`, a generic `ms` fallback, `msgs`, the usage
percent, the model name, `used`/`window` from a parenthesised pair, and
`inbound_bytes`/`outbound_bytes` from `KiB`/`MiB` suffixes. Unknown shapes
become nulls rather than guesses.

**group** aggregates. The spec is `col:agg`, so the column comes **first**:

```
--agg count,bytes:sum,bytes:max
```

A bare name counts. `count` counts rows. A bare column name counts that column
and rejects nulls. Both the comma form and a repeated `--agg` flag work. The
aggregates are `count`, `sum`, `mean`, `min`, `max`, `nunique`, and `std`.

**fit** runs ordinary least squares.

It reports n, degrees of freedom, R-squared, adjusted R-squared, and RMSE.

It also reports a p-value per coefficient, and a VIF per feature.

The VIF makes collinear predictors visible instead of silently split.

**anomaly** flags outliers.

It defaults to the median absolute deviation, which is the right default here.

One 10x spike inflates a mean and a standard deviation enough to flag the whole
healthy population.

`--method iqr` is available. `--threshold` defaults to 3.5.

## Every subcommand writes parquet

Pass `-o OUT` to any subcommand and the result lands in a parquet file.

This is the point of the tool.

A description becomes a filtered dataset. The filter becomes a group.

The group becomes a fit input, and nothing is lost to a terminal that scrolled
away.

## Why the fit is implemented the way it is

`fit` solves the normal equations through `np.linalg.lstsq` on the augmented
matrix, never through a matrix inverse.

A matrix inverse on collinear columns produces an error or a silent garbage
answer. `lstsq` degrades to the minimum-norm solution instead.

So a collinear pair shows up as a large VIF rather than as a crash.

The standard errors use the pseudo-inverse for the same reason.

The p-values need a t-distribution. scipy is not installed in this venv.

`pq.py` carries its own incomplete-beta continued fraction instead.

It is validated against published t-table values in the test suite.

## Worked example

The compress path in the proxy is measured by parsing its log, filtering to the
request lines, then asking what explains the latency:

```
$P scripts/pq.py log ~/.local/state/billion-context/bili.log -o bili.parquet
$P scripts/pq.py group bili.parquet --by kind --agg count,msgs:mean
$P scripts/pq.py anomaly bili.parquet --col local_ms
```

`anomaly` on `local_ms` is how the 7 pathological requests were found.

They were 0.23% of the traffic and 84.8% of the total time.

A mean or a standard-deviation rule would have buried them.

## Constraints

- The venv interpreter is required. The system `python3` has no pyarrow.
- `fit` needs numeric columns. A string column is a type error.
- Reading a 9 MB parquet takes a second or two. Anything wider than a few
  million rows should be sampled first with `group`.
