from contextlib import asynccontextmanager
from fastapi import File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from app.base import create_base, ROOT
from app.forecast import generate,experiment,future,parse_csv,DataError,LIMIT

def create_app(state=None):
    @asynccontextmanager
    async def lifespan(app):
        if app.state.experiment is None:app.state.experiment=experiment(generate())
        yield
    app=create_base('DemandLab',lifespan);app.state.experiment=state
    @app.get('/api/status')
    def status():
        e=app.state.experiment
        if not e:return {'ready':False}
        return {'ready':True,**{k:e[k] for k in ('model','validation_mae','interval_width','test','test_start','test_end','windows')},'sample':future(e,e['data'],True)}
    @app.get('/example.csv')
    def sample():return FileResponse(ROOT/'examples'/'fictional_sales.csv',media_type='text/csv',filename='fictional_sales.csv')
    @app.post('/api/forecast')
    async def upload(file:UploadFile=File(...)):
        if not file.filename or not file.filename.lower().endswith('.csv'):raise HTTPException(400,'Choose a CSV file.')
        data=await file.read(LIMIT+1);await file.close()
        try:rows=parse_csv(data)
        except DataError as e:raise HTTPException(400,str(e)) from e
        return future(app.state.experiment,rows,False)
    return app
app=create_app()
