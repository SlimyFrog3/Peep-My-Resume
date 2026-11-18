"""One stateless upload endpoint plus optional production frontend hosting."""
from pathlib import Path
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool
from .parser import parse_resume, ParseError, MAX_BYTES

from .workflow import ReviewRequest, preview_export, export_docx
from .ai_review import AIRequest, suggest, enabled

VERSION = '4.0.0-beta'
app = FastAPI(title='Peep-My-Resume API', version=VERSION)

@app.middleware('http')
async def limit_review_body(request: Request, call_next):
    if request.url.path in {'/review/preview', '/review/export', '/ai/review'}:
        chunks, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 2 * 1024 * 1024:
                return Response('Review request is too large.', status_code=413)
            chunks.append(chunk)
        request._body = b''.join(chunks)
    return await call_next(request)


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
            raise HTTPException(status_code=422, detail=str(error),
                                headers={'X-Readability-Score': '0'} if str(error).startswith('No readable text') else None) from error
        except Exception as error:
            # Log the failure type, never the uploaded resume or contact details.
            logging.getLogger(__name__).error('Unexpected parser failure: %s', type(error).__name__)
            raise HTTPException(status_code=500, detail='The service could not process this document. Please try again. If it keeps failing, report the issue.') from error
    finally:
        await file.close()

@app.get('/capabilities')
def capabilities():
    return {'aiEnabled': enabled(), 'docxExport': True, 'rubricVersion': '1.0'}


@app.post('/review/preview')
def preview(request: ReviewRequest):
    return preview_export(request)


@app.post('/review/export')
def export(request: ReviewRequest):
    return Response(export_docx(request.blocks),
                    media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    headers={'Content-Disposition': 'attachment; filename="Peep-My-Resume.docx"'})


@app.post('/ai/review')
async def ai_review(request: AIRequest, http_request: Request):
    return await suggest(request, http_request.client.host if http_request.client else 'unknown')


# Vite proxies /parse locally. In production FastAPI serves the built frontend.
dist = Path(__file__).resolve().parent.parent / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
