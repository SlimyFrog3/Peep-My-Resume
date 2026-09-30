"""One stateless upload endpoint plus optional production frontend hosting."""
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .parser import parse_resume, ParseError, MAX_BYTES

app = FastAPI(title='Peep-My-Resume API', version='1.0.0')

@app.get('/health')
def health():
    return {'status': 'ok', 'version': '1.0.0'}

@app.post('/parse')
async def parse(file: UploadFile = File(...)):
    try:
        data = await file.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=413, detail='The file exceeds the 10 MB limit.')
        try:
            return await run_in_threadpool(parse_resume, data, file.filename or '')
        except ParseError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        await file.close()

# Vite proxies /parse locally. In production FastAPI serves the built frontend.
dist = Path(__file__).resolve().parent.parent / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
