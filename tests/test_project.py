import pytest
from fastapi.testclient import TestClient
from app.forecast import generate,parse_csv,DataError,predict,experiment,future,metrics
from app.main import create_app
from pathlib import Path

@pytest.fixture(scope='module')
def state():return experiment(generate())
@pytest.fixture(scope='module')
def client(state):
    with TestClient(create_app(state),base_url='http://127.0.0.1:8030') as c:yield c
EX=Path(__file__).resolve().parents[1]/'examples'/'fictional_sales.csv'
def test_generator_repeatable():assert generate(100)==generate(100) and generate(100)!=generate(100,1)
def test_csv_valid():assert len(parse_csv(EX.read_bytes()))==84
def test_missing_headers():
    with pytest.raises(DataError,match='Required'):parse_csv(b'bad,columns\n1,2')
def test_bad_dates():
    data=EX.read_text().replace('2025-01-02','2025-01-01').encode()
    with pytest.raises(DataError,match='unique and consecutive'):parse_csv(data)
def test_bad_value():
    data=EX.read_text().replace('2025-01-01,44','2025-01-01,nan').encode()
    with pytest.raises(DataError,match='sales'):parse_csv(data)
def test_split_windows_end_before_test(state):
    assert max(w['test_end'] for w in state['windows'])<state['test_start']
    assert all(w['train_end']<w['test_start'] for w in state['windows'])
def test_model_selected_from_validation(state):assert state['model']==min(state['validation_mae'],key=state['validation_mae'].get)
def test_future_seven_days_and_bounds(state):
    f=future(state,state['data'],True);assert len(f['forecast'])==7
    assert all(x['low']<=x['forecast']<=x['high'] for x in f['forecast'])
    assert abs(f['total']-sum(x['forecast'] for x in f['forecast']))<1e-10
def test_upload_has_no_interval(state):assert not future(state,parse_csv(EX.read_bytes()),False)['has_interval']
def test_metrics():
    m=metrics([2,4],[1,5]);assert m['mae']==1 and abs(m['wape']-1/3)<1e-9
    assert metrics([0,0],[1,2])['wape'] is None
def test_api(client):
    assert client.get('/').status_code==200 and client.get('/api/status').json()['ready']
    r=client.post('/api/forecast',files={'file':('x.csv',EX.read_bytes(),'text/csv')});assert r.status_code==200 and len(r.json()['forecast'])==7 and not r.json()['has_interval']
def test_invalid_file_and_origin(client):
    assert client.post('/api/forecast',files={'file':('x.txt',b'x')}).status_code==400
    assert client.get('/api/status',headers={'Origin':'https://evil.example'}).status_code==403
