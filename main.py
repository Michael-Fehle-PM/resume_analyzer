import os
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from backend.database import init_db, get_db, Application
from backend.analyser import scrape_skills, analyse_match, reorder_cv, generate_docx
from backend.pdf_utils import extract_text_from_multiple

app = FastAPI(title="Resume Analyser")

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

init_db()


# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── CV Analysis endpoints ──────────────────────────────────────────────────────

@app.post("/api/extract-pdf")
async def extract_pdf(files: list[UploadFile] = File(...)):
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append((f.filename, content))
    try:
        text = extract_text_from_multiple(file_data)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/fetch-jd")
async def fetch_jd(url: str = Form(...)):
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; ResumeAnalyser/1.0)"}
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self._skip = False

                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style", "nav", "header", "footer"):
                        self._skip = True

                def handle_endtag(self, tag):
                    if tag in ("script", "style", "nav", "header", "footer"):
                        self._skip = False

                def handle_data(self, data):
                    if not self._skip and data.strip():
                        self.text.append(data.strip())

            parser = TextExtractor()
            parser.feed(resp.text)
            text = "\n".join(parser.text)
            return {"text": text[:8000]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch URL: {e}")


@app.post("/api/scrape-skills")
async def api_scrape_skills(cv_text: str = Form(...)):
    try:
        result = scrape_skills(cv_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyse")
async def api_analyse(cv_text: str = Form(...), jd_text: str = Form(...)):
    try:
        result = analyse_match(cv_text, jd_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reorder-cv")
async def api_reorder_cv(cv_text: str = Form(...), jd_text: str = Form(...)):
    try:
        result = reorder_cv(cv_text, jd_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download-docx")
async def api_download_docx(cv_text: str = Form(...), jd_text: str = Form(...)):
    try:
        docx_bytes = generate_docx(cv_text, jd_text)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": "attachment; filename=resume_tailored.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Job Tracker endpoints ──────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    role: str
    company: str
    jd_url: Optional[str] = None
    date_applied: Optional[str] = None
    status: str = "applied"
    notes: Optional[str] = None


class ApplicationUpdate(ApplicationCreate):
    pass


@app.get("/api/applications")
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(Application).order_by(Application.created_at.desc()).all()
    return [
        {
            "id": a.id, "role": a.role, "company": a.company,
            "jd_url": a.jd_url, "date_applied": a.date_applied,
            "status": a.status, "notes": a.notes,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in apps
    ]


@app.post("/api/applications")
def create_application(app_data: ApplicationCreate, db: Session = Depends(get_db)):
    app_obj = Application(
        id=str(uuid.uuid4()),
        role=app_data.role,
        company=app_data.company,
        jd_url=app_data.jd_url,
        date_applied=app_data.date_applied,
        status=app_data.status,
        notes=app_data.notes,
    )
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return {"id": app_obj.id, "message": "Created"}


@app.put("/api/applications/{app_id}")
def update_application(app_id: str, app_data: ApplicationUpdate, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    app_obj.role = app_data.role
    app_obj.company = app_data.company
    app_obj.jd_url = app_data.jd_url
    app_obj.date_applied = app_data.date_applied
    app_obj.status = app_data.status
    app_obj.notes = app_data.notes
    app_obj.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Updated"}


@app.delete("/api/applications/{app_id}")
def delete_application(app_id: str, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.id == app_id).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")
    db.delete(app_obj)
    db.commit()
    return {"message": "Deleted"}
