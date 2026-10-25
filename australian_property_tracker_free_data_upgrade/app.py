import datetime as dt
import io
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title='Australian Property Growth Research',page_icon='🏠',layout='wide')
BASE='https://geo.abs.gov.au/arcgis/rest/services/Hosted/SA2_Regional_Population_2025/FeatureServer'
STATES={'New South Wales':'NSW','Victoria':'VIC','Queensland':'QLD','South Australia':'SA','Western Australia':'WA','Tasmania':'TAS','Northern Territory':'NT','Australian Capital Territory':'ACT'}

def get(url, params):
    r=requests.get(url,params=params,timeout=45,headers={'User-Agent':'PropertyGrowthResearch/1.0'})
    r.raise_for_status(); data=r.json()
    if 'error' in data: raise ValueError(str(data['error']))
    return data

@st.cache_data(ttl=86400,show_spinner='Downloading official ABS regional population data...')
def abs_population():
    svc=get(BASE,{'f':'json'})
    layers=svc.get('layers',[])
    if not layers: raise ValueError('ABS service currently exposes no layers')
    lid=layers[0]['id']; endpoint=f'{BASE}/{lid}'
    info=get(endpoint,{'f':'json'})
    fields=[x['name'] for x in info.get('fields',[])]
    def pick(candidates):
        return next((x for x in candidates if x in fields),None)
    area=pick(['sa2_name_2021','SA2_NAME_2021','sa2_name','SA2_NAME'])
    state=pick(['state_name_2021','STATE_NAME_2021','state_name','STATE_NAME'])
    code=pick(['sa2_code_2021','SA2_CODE_2021','sa2_code','SA2_CODE'])
    # ABS service schema can change: locate estimated resident population year fields by alias.
    yr={}
    for f in info.get('fields',[]):
        name=f['name']; alias=f.get('alias',''); s=(name+' '+alias).lower()
        if '2025' in s and ('erp' in s or 'population' in s or 'persons' in s): yr[2025]=name
        if '2020' in s and ('erp' in s or 'population' in s or 'persons' in s): yr[2020]=name
        if '2024' in s and ('erp' in s or 'population' in s or 'persons' in s): yr[2024]=name
    # Explicit fallback for common ABS naming conventions.
    for y in (2020,2024,2025):
        if y not in yr:
            matches=[f for f in fields if str(y) in f and any(t in f.lower() for t in ['erp','pop'])]
            if matches: yr[y]=matches[0]
    if not area or not state or 2025 not in yr or 2020 not in yr:
        raise ValueError('ABS changed its field names. Available fields: '+', '.join(fields[:90]))
    cols=list(dict.fromkeys([area,state,code,yr[2020],yr[2025],yr.get(2024)]))
    cols=[c for c in cols if c]
    count=get(endpoint+'/query',{'where':'1=1','returnCountOnly':'true','f':'json'}).get('count',0)
    if count<=0: raise ValueError('ABS query returned no records')
    items=[]
    for offset in range(0,count,500):
        result=get(endpoint+'/query',{'where':'1=1','outFields':','.join(cols),'returnGeometry':'false','resultOffset':offset,'resultRecordCount':500,'f':'json'})
        items.extend(x['attributes'] for x in result.get('features',[]))
    df=pd.DataFrame(items)
    if df.empty: raise ValueError('No population records returned')
    df=df.rename(columns={area:'area',state:'state',yr[2020]:'pop_2020',yr[2025]:'pop_2025'})
    if code: df=df.rename(columns={code:'sa2_code'})
    if 2024 in yr: df=df.rename(columns={yr[2024]:'pop_2024'})
    for col in ['pop_2020','pop_2025']:
        df[col]=pd.to_numeric(df[col],errors='coerce')
    df=df[df.pop_2020.gt(0)&df.pop_2025.gt(0)].copy()
    df['growth_5y_pct']=(df.pop_2025/df.pop_2020-1)*100
    df['annualised_growth_pct']=((df.pop_2025/df.pop_2020)**.2-1)*100
    if 'pop_2024' in df:
        df['pop_2024']=pd.to_numeric(df.pop_2024,errors='coerce')
        df['growth_1y_pct']=(df.pop_2025/df.pop_2024-1)*100
    df['state']=df.state.replace(STATES)
    return df,dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

st.title('🏠 Australian Property Growth Research')
st.caption('Free ABS population signals • Australia-wide • No fabricated prices, rents, or investment returns')
with st.sidebar:
    st.header('Market settings')
    if st.button('Refresh ABS data now'):
        abs_population.clear();st.rerun()
    state_filter=st.selectbox('State / territory',['All states']+list(STATES.values()))
    min_pop=st.number_input('Minimum population (2025)',100,100000,2000,500)
    st.info('ABS SA2 regions are not always identical to real-estate suburbs. Population growth is not house-price growth.')
try:
    data,fetched=abs_population()
    if state_filter!='All states':data=data[data.state==state_filter]
    data=data[data.pop_2025>=min_pop].copy()
    st.success(f'Official ABS data loaded • {len(data):,} regions • checked {fetched} • published reference year 2025')
    st.markdown('### Population growth watchlist (not a forecast of property prices)')
    cols=['area','state','pop_2020','pop_2025','growth_5y_pct','annualised_growth_pct']
    if 'growth_1y_pct' in data:cols.append('growth_1y_pct')
    st.dataframe(data.sort_values('growth_5y_pct',ascending=False)[cols].head(100),use_container_width=True,hide_index=True)
    st.download_button('Download filtered ABS regions CSV',data[cols].to_csv(index=False).encode(),'abs_population_growth_regions.csv','text/csv')
    st.markdown('### Analyse verified property-market CSV data')
    st.write('Optional: upload a CSV with `area`, `state`, `median_price`, `weekly_rent`, `growth_5y_pct` (property-price growth, not population growth).')
    up=st.file_uploader('Upload verified property statistics',type='csv')
    if up:
        p=pd.read_csv(up)
        needed={'area','state','median_price','weekly_rent','growth_5y_pct'}
        if not needed.issubset(p.columns): st.error('Missing columns: '+', '.join(sorted(needed-set(p.columns))))
        else:
            for c in ['median_price','weekly_rent','growth_5y_pct']:p[c]=pd.to_numeric(p[c],errors='coerce')
            p['gross_rental_yield_pct']=p.weekly_rent*52/p.median_price*100
            st.dataframe(p.sort_values('growth_5y_pct',ascending=False),use_container_width=True,hide_index=True)
            st.caption('These values come from your uploaded file, not ABS. Verify coverage, licence, dates, and comparability before using them.')
    st.markdown('### Property cash flow scenario calculator')
    a,b,c=st.columns(3)
    with a: price=st.number_input('Purchase price (AUD)',min_value=10000,value=650000,step=10000)
    with b: rent=st.number_input('Weekly rent (AUD)',min_value=0,value=600,step=25)
    with c: deposit=st.slider('Deposit (%)',5,100,20)
    a,b,c=st.columns(3)
    with a: interest=st.number_input('Annual interest rate (%)',0.0,20.0,6.0,0.25)
    with b: costs=st.number_input('Annual operating costs (AUD)',0,100000,7500,500)
    with c: growth=st.number_input('Hypothetical capital growth (%)',-30.0,30.0,4.0,0.5)
    loan=price*(1-deposit/100);gross=rent*52;cash=gross-costs-loan*interest/100
    m1,m2,m3,m4=st.columns(4)
    m1.metric('Gross rental yield',f'{gross/price*100:.2f}%')
    m2.metric('Net unlevered yield',f'{(gross-costs)/price*100:.2f}%')
    m3.metric('Interest-only annual cash flow',f'${cash:,.0f}')
    m4.metric('Illustrative value change',f'${price*growth/100:,.0f}')
    st.caption('Scenario only. Excludes purchase costs, stamp duty, income tax, principal repayments, capital gains tax, and sale costs. Not a prediction.')
except Exception as e:
    st.error('ABS data could not be downloaded or parsed. The app will not invent results.')
    st.code(str(e))
    st.info('Try Refresh ABS data now. If the ABS service schema changed, send the error shown above so the field mapping can be updated.')

st.divider()
st.markdown('**Sources:** [ABS Regional population 2024–25](https://www.abs.gov.au/statistics/people/population/regional-population/2024-25) · [ABS SA2 Feature Service](https://geo.abs.gov.au/arcgis/rest/services/Hosted/SA2_Regional_Population_2025/FeatureServer)')
st.caption('Research only. Regional population trends cannot establish future capital growth. Free nationwide suburb-level sales, rent and vacancy data are not supplied by this source.')
