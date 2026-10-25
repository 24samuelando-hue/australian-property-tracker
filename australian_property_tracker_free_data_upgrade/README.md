# Australian Property Growth Research — free-data upgrade

## Install on existing GitHub + Streamlit site

1. Open your GitHub repository `australian-property-tracker`.
2. Upload **app.py** and **requirements.txt** from this ZIP to the repository root, replacing the existing files. (Use GitHub Add file → Upload files; commit.)
3. In Streamlit Community Cloud confirm **Main file path** is `app.py` and branch is `main`.
4. Open the website. The app requests ABS SA2 population data on first load, and caches results for 24 hours. The **Refresh ABS data now** button clears the cache.
5. You can optionally upload a CSV of *verified* property-market data for property price growth and rental yield analysis.

## What is and isn't automated

The ABS service is queried when the app runs; the cache refreshes after 24 hours when someone opens the app. This is **not** a background job that runs while the app is sleeping. New annual ABS releases may change the service endpoint or schema and require a code update. A separate scheduled workflow is needed for unattended monitoring and alerts.

## Data provenance and restrictions

Official ABS SA2 Regional population 2024–25, https://geo.abs.gov.au/arcgis/rest/services/Hosted/SA2_Regional_Population_2025/FeatureServer . This is **population**, not residential property price growth. No real-estate ROI rankings can be derived from this dataset alone. State government property-sales licensing and availability vary. Do not scrape property portals or republish datasets without permission.

## Notes

The app discovers ABS field names from the ArcGIS service metadata at runtime, and fails with a visible error if expected fields are unavailable. It does not substitute fabricated data. The source cannot be accessed in the offline build environment, so live schema compatibility should be checked after deployment.
