"""Shared CSV schema and validation for the website and scheduled importer."""
import pandas as pd
COLS=['suburb','state','property_type','median_price','weekly_rent','growth_1y_pct','growth_3y_pct','growth_5y_pct','vacancy_pct','days_on_market','sales_12mo','population_growth_5y_pct','inventory_months','as_of']
NUM=[c for c in COLS if c not in ['suburb','state','property_type','as_of']]
def validate(df):
    missing=set(COLS)-set(df.columns)
    if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    df=df[COLS].copy()
    for c in NUM: df[c]=pd.to_numeric(df[c],errors='coerce')
    df['suburb']=df['suburb'].astype('string').str.strip()
    df['state']=df['state'].astype('string').str.upper().str.strip()
    df['property_type']=df['property_type'].astype('string').str.lower().str.strip()
    df['as_of']=pd.to_datetime(df['as_of'],errors='coerce').dt.strftime('%Y-%m-%d')
    df=df.dropna(subset=['suburb','state','property_type','median_price','as_of'])
    df=df[(df.suburb!='')&(df.median_price>0)&df.state.isin(['NSW','VIC','QLD','SA','WA','TAS','NT','ACT'])&df.property_type.isin(['house','unit'])]
    return df.drop_duplicates(['suburb','state','property_type'],keep='last')
