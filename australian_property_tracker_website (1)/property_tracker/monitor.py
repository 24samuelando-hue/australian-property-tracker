"""Run via cron or Task Scheduler after importing new data snapshots."""
import sqlite3, os, csv, datetime
DB=os.getenv('TRACKER_DB','property_tracker.sqlite')
if not os.path.exists(DB):raise SystemExit('No database. Import CSV in app first.')
con=sqlite3.connect(DB);con.row_factory=sqlite3.Row
rows=con.execute('SELECT * FROM snapshots ORDER BY recorded_at DESC').fetchall();con.close()
seen={}; alerts=[]
for r in rows:
    key=(r['suburb'],r['state'],r['property_type'])
    if key not in seen:seen[key]=r;continue
    newer=seen.pop(key)
    if newer is None:
        seen[key]=None
        continue
    if newer['median_price'] and r['median_price']:
        change=(newer['median_price']/r['median_price']-1)*100
        if abs(change)>=2:alerts.append({'suburb':key[0],'state':key[1],'type':key[2],'old_price':r['median_price'],'new_price':newer['median_price'],'change_pct':round(change,2),'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    # Only compare newest two records per market.
    seen[key]=None
if alerts:
    name='market_alerts.csv'
    with open(name,'w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=alerts[0]);w.writeheader();w.writerows(alerts)
    print(f'{len(alerts)} alerts saved to {name}')
else:print('No price changes >= 2% between latest snapshots.')
