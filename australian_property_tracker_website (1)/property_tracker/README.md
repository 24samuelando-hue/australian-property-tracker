# Australian Property Growth Tracker

An Australia-wide capital-growth-first suburb dashboard. **No real market data is bundled.** It only ranks licensed data you import. Nothing runs in the background unless you deploy and schedule it.

## Run

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Upload a CSV using the app sidebar, then click **Save new market snapshot**. Download the blank CSV template from the sidebar. All 15 columns are required; numeric fields can be empty. State: NSW, VIC, QLD, WA, SA, TAS, ACT, NT. Property type: `house` or `unit`. Dates in `as_of` should be ISO `YYYY-MM-DD`. A row represents one suburb and property type. A local SQLite file stores the snapshots.

## Data sourcing

Use a licensed provider for suburb-level price, rent, sales volume, vacancy, and growth data. Examples: Domain data via AURIN (access restricted), or a commercial property API such as PropRadar (check coverage, subscription, license and current documentation). ABS provides population and approvals; RBA provides interest-rate context. Never scrape sites in violation of their terms. Map provider fields to the CSV schema using an approved export or API adapter.

## How scores work

Capital growth score = weighted percentile ranks over the *currently filtered?* No: over all imported markets, prior to sidebar filters. Weights: 3y historical price growth 26%, 5y 19%, 1y 12%, 5y population growth 15%, vacancy 10% (lower better), days on market 7% (lower better), inventory 6% (lower better), 12m sales 5% (higher better). Missing signals are neutral and flagged if more than two are absent. These are heuristic **screening scores**, not forward-return forecasts. Suburbs with different dwelling mixes or thin sales may be misleading. Check sample sizes, outliers, development pipeline, insurance/flood/bushfire risk, economic concentration and local infrastructure manually.

Gross yield = 52 × weekly rent / price. Net yield = (effective rent less operating expenses) / price. Cash flow assumes interest-only loan and excludes tax and principal repayments. Cash-on-cash uses deposit plus estimated upfront purchase costs. Annual cash flow may be negative even in fast-growing suburbs.

## Monitoring

After a fresh licensed CSV import, run `python monitor.py`. It compares the latest two saved price snapshots per suburb/type and writes `market_alerts.csv` for median price changes of at least 2%. This is a **snapshot change detector**, not a predictive alert. Schedule this command in cron/Task Scheduler if the database is regularly updated. To automate data ingestion, obtain a provider API key and build an adapter permitted by its licensing terms. Do not commit credentials. The current version does not automatically pull data or email notifications.

## Suggested next iteration

Provider API adapter, nightly ingest, date-aligned historical price chart, sample-quality confidence bands, infrastructure approvals, hazard overlay, price-drop listing alerts, email delivery, cloud deployment and forward scenario stress tests.

## Deploy as a phone-friendly website (Streamlit Community Cloud)

1. Upload the entire `property_tracker` folder contents to a GitHub repository (with `app.py` at repository root). **Use a private repository if your market-data licence requires it**; check Streamlit Cloud's repository access and deployment visibility options.
2. Visit https://share.streamlit.io/ and create a new app from the repository; entrypoint: `app.py`.
3. The site will have a public URL accessible on a phone or desktop. Until real data is supplied, it correctly displays *no market data loaded*.
4. Obtain permission from your data provider for cloud hosting and any redistribution. For automated daily updates, add GitHub Actions repository secrets `MARKET_CSV_URL` (an HTTPS endpoint returning the exact CSV schema) and, if required, `MARKET_API_TOKEN` (Bearer token). Enable GitHub Actions write permission for workflow commits. The included workflow runs at 07:15 AEST daily (schedule timing may drift) and commits `data/latest.csv`.
5. For licensed private data **do not commit the CSV to a public repository**. This starter workflow commits data into the repository and is appropriate only if your licence and repository access permit that. For sensitive data, use a private database and server-side API instead.
6. The website reads `data/latest.csv` on restart. Uploading a CSV directly into a cloud session stores it only in temporary local SQLite storage; it may disappear on restart. The scheduled CSV is the persistent website source.

**Important limitations:** The refresh workflow does not magically provide a property-data subscription. You must supply an authorised feed already formatted to the documented schema. It monitors source updates, not live listings or individual house prices. No email/push alerts are configured. It is a heuristic ranking, not a machine-learning capital-growth prediction. Use the site as a screening aid, not a financial recommendation.
