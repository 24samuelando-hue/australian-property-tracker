"""Download a licensed CSV feed supplied by the owner. No scraping."""
import io, os, pathlib, urllib.request
import pandas as pd
from app_data import COLS, validate

url=os.environ.get('MARKET_CSV_URL','').strip()
if not url:
    print('MARKET_CSV_URL is not configured; skipping ingestion.')
    raise SystemExit(0)
if not url.startswith('https://'):
    raise SystemExit('MARKET_CSV_URL must use HTTPS')
headers={'User-Agent':'PropertyGrowthTracker/1.0'}
if os.environ.get('MARKET_API_TOKEN'):
    headers['Authorization']='Bearer '+os.environ['MARKET_API_TOKEN']
with urllib.request.urlopen(urllib.request.Request(url,headers=headers),timeout=45) as response:
    data=response.read(20_000_001)
if len(data)>20_000_000: raise SystemExit('Feed exceeds 20MB limit')
df=validate(pd.read_csv(io.BytesIO(data)))
if df.empty: raise SystemExit('Feed contained no valid records')
path=pathlib.Path(__file__).parent/'data'/'latest.csv'
path.parent.mkdir(exist_ok=True)
df.to_csv(path,index=False)
print(f'Saved {len(df)} validated records to {path}')
