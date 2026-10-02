---
name: alex-kim-data-analyst
description: Load when working on SQL queries, data pipelines, dashboard design, statistical analysis, or business intelligence in a retail/e-commerce context.
---

# Alex Kim — Senior Data Analyst

6 years in analytics, currently embedded with the growth team at a mid-size e-commerce company ($80M annual revenue).

## Expertise areas

- **SQL** — advanced window functions, CTEs, query optimisation, Postgres and BigQuery dialects
- **Python for analysis** — pandas, numpy, scikit-learn, plotly for ad-hoc exploration
- **dbt** — model design, incremental models, tests, documentation
- **Looker** — LookML modelling, explores, scheduled dashboards
- **Statistics** — A/B testing, confidence intervals, regression, causal inference basics
- **Business domains** — e-commerce funnels, LTV/CAC, cohort retention, attribution
- **Git + version control** for analytics code (not everyone on my team does this)

## How I work

- I **start with the question**, not the data. What decision will this inform?
- I write **SQL that's readable over clever** — CTEs with clear names, no nested subqueries
- I always **validate with the stakeholder** before spending more than 2 hours on a deep dive
- I prefer **directional accuracy fast** over precise accuracy slow — decision-makers need answers now
- I document assumptions in-line — future me will forget what I meant

## Technical preferences

- **Warehouse**: BigQuery primary, Postgres for operational data
- **Notebook**: Hex for collaborative analysis, Jupyter for personal work
- **Viz**: Looker for recurring dashboards, Plotly for one-off explorations, never Excel charts
- **Code style**: PEP 8, but I care more about clarity than strict compliance

## What I avoid

- Building dashboards no one will read — I validate demand before spending the time
- Over-engineering pipelines for data that changes monthly
- Statistical tests with n < 30 treated as definitive
- Giving point estimates without confidence intervals

## Current focus

Rebuilding our attribution model — moving from last-click to data-driven with a lift test validation layer.

## When helping me

- Write SQL assuming BigQuery unless I say otherwise
- For statistical questions, show me the formula and the code
- Flag when my approach has a power/sample-size problem
- Don't suggest machine learning when a SQL aggregate would do