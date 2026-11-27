"""Time-aware forecasting of entirely synthetic daily demand."""
import csv,io
from datetime import date,timedelta
import numpy as np
from sklearn.ensemble import RandomForestRegressor

HORIZON=7; SEED=427; LIMIT=2*1024*1024
class DataError(ValueError):pass

def generate(n=700,seed=SEED):
    rng=np.random.default_rng(seed);start=date(2024,1,1);rows=[]
    for i in range(n):
        d=start+timedelta(days=i)
        # Invented weekly pattern, trend, seasonal movement and random noise.
        sales=max(0,45+.023*i+8*np.sin(2*np.pi*d.weekday()/7)+5*np.sin(2*np.pi*i/180)+rng.normal(0,4))
        rows.append({'date':d.isoformat(),'sales':round(float(sales),2)})
    return rows

def parse_csv(data):
    if len(data)>LIMIT:raise DataError('CSV exceeds 2 MB.')
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError as e:raise DataError('CSV must use UTF-8.') from e
    reader=csv.DictReader(io.StringIO(text,newline=''))
    if not reader.fieldnames:raise DataError('CSV must have a header.')
    reader.fieldnames=[x.strip() for x in reader.fieldnames]
    if len(set(reader.fieldnames))!=len(reader.fieldnames):raise DataError('Duplicate column names.')
    if not {'date','sales'}.issubset(reader.fieldnames):raise DataError('Required columns: date, sales.')
    rows=[]
    for line,r in enumerate(reader,2):
        if len(rows)>=2000:raise DataError('At most 2,000 rows are supported.')
        try:
            if None in r:raise ValueError('too many columns')
            d=date.fromisoformat((r.get('date') or '').strip())
            value=float((r.get('sales') or '').strip())
            if not np.isfinite(value) or not 0<=value<=1_000_000:raise ValueError('sales must be between 0 and 1,000,000')
            rows.append({'date':d.isoformat(),'sales':value})
        except ValueError as e:raise DataError(f'Row {line}: {e}') from e
    if len(rows)<60:raise DataError('Provide at least 60 consecutive daily rows.')
    rows.sort(key=lambda r:r['date'])
    for a,b in zip(rows,rows[1:]):
        if date.fromisoformat(b['date'])-date.fromisoformat(a['date'])!=timedelta(days=1):raise DataError('Dates must be unique and consecutive with no missing days.')
    return rows

def design(history,d):
    return [history[-1],history[-7],history[-14],history[-28],float(np.mean(history[-7:])),d.weekday()]

def fit_forest(rows):
    values=[r['sales'] for r in rows];X=[];y=[]
    for i in range(28,len(rows)):
        X.append(design(values[:i],date.fromisoformat(rows[i]['date'])));y.append(values[i])
    model=RandomForestRegressor(n_estimators=60,min_samples_leaf=4,random_state=SEED,n_jobs=1)
    model.fit(X,y);return model

def predict(history,model_name,horizon=HORIZON):
    values=[float(r['sales']) for r in history];last=date.fromisoformat(history[-1]['date']);out=[]
    model=fit_forest(history) if model_name=='Random forest' else None
    for step in range(1,horizon+1):
        d=last+timedelta(days=step)
        value=values[-7] if model is None else float(model.predict([design(values,d)])[0])
        value=max(0,value);out.append({'date':d.isoformat(),'forecast':value});values.append(value)
    return out

def metrics(actual,pred):
    actual=np.asarray(actual,dtype=float);pred=np.asarray(pred,dtype=float);e=np.abs(actual-pred)
    return {'mae':float(e.mean()),'wape':float(e.sum()/actual.sum()) if actual.sum()>0 else None}

def experiment(rows):
    n=len(rows);models=['Seasonal naive','Random forest'];errors={m:[] for m in models};abs_res={m:[] for m in models}
    windows=[]
    # Three separate validation origins; hold out final 7 days during selection.
    for end in (n-28,n-21,n-14):
        train=rows[:end];actual=[x['sales'] for x in rows[end:end+HORIZON]];windows.append({'train_end':train[-1]['date'],'test_start':rows[end]['date'],'test_end':rows[end+HORIZON-1]['date']})
        for m in models:
            p=[x['forecast'] for x in predict(train,m)]
            errors[m].extend(abs(a-b) for a,b in zip(actual,p));abs_res[m].extend(abs(a-b) for a,b in zip(actual,p))
    comparison={m:float(np.mean(errors[m])) for m in models};selected=min(models,key=lambda m:comparison[m])
    # Simple empirical absolute error quantile, derived on validation only.
    width=float(np.quantile(abs_res[selected],.9))
    origin=n-7; actual=[x['sales'] for x in rows[origin:]];pred=predict(rows[:origin],selected)
    test=metrics(actual,[x['forecast'] for x in pred])
    return {'model':selected,'validation_mae':comparison,'interval_width':width,'test':test,
            'test_start':rows[origin]['date'],'test_end':rows[-1]['date'],'windows':windows,'data':rows}

def future(experiment,rows,include_interval=False):
    pred=predict(rows,experiment['model']); width=experiment['interval_width']
    for p in pred:
        if include_interval:p['low']=max(0,p['forecast']-width);p['high']=p['forecast']+width
    total=sum(p['forecast'] for p in pred)
    return {'model':experiment['model'],'forecast':pred,'total':total,'illustrative_stock':total*1.1,
            'has_interval':include_interval}
