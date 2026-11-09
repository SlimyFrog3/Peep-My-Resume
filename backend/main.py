"""One stateless upload endpoint plus optional production frontend hosting."""
from pathlib import Path
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .parser import parse_resume, ParseError, MAX_BYTES

VERSION = '3.0.0-beta'
app = FastAPI(title='Peep-My-Resume API', version=VERSION)

@app.get('/health')
def health():
    return {'status': 'ok', 'version': VERSION}

@app.post('/parse')
async def parse(file: UploadFile = File(...)):
    try:
        try:
            data = await file.read(MAX_BYTES + 1)
        except OSError as error:
            raise HTTPException(status_code=500, detail='The service could not read the upload. Please try again.') from error
        if len(data) > MAX_BYTES:
            raise HTTPException(status_code=413, detail='The file exceeds the 10 MB limit.')
        try:
            return await run_in_threadpool(parse_resume, data, file.filename or '')
        except ParseError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except Exception as error:
            # Log the failure type, never the uploaded resume or contact details.
            logging.getLogger(__name__).error('Unexpected parser failure: %s', type(error).__name__)
            raise HTTPException(status_code=500, detail='The service could not process this document. Please try again. If it keeps failing, report the issue.') from error
    finally:
        await file.close()

# Vite proxies /parse locally. In production FastAPI serves the built frontend.
dist = Path(__file__).resolve().parent.parent / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
