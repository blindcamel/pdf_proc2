import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pathlib import Path
import shutil
import uuid

from app.core.config import settings
from app.db.session import init_db, get_session
from app.models.schemas import Job, JobStatus, Invoice
from app.services.ai.cascade import CascadeService
from app.services.pdf.processor import PDFService
from app.services.normalizer import CompanyNormalizer

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Ensure static directory exists before the app mounts it
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes the database on startup."""
    logger.info("Starting up PDFProc v.2...")
    init_db()
    yield
    logger.info("Shutting down...")


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

# Initialize Services
pdf_service = PDFService()
ai_service = CascadeService()
normalizer = CompanyNormalizer()


async def process_pdf_task(job_id: int, file_path: Path, db: Session):
    """Background task to handle the AI and PDF logic without blocking the user."""
    job = db.get(Job, job_id)
    if not job:
        return

    try:
        job.status = JobStatus.PROCESSING
        db.add(job)
        db.commit()

        # 1. Extract Text (Tier 1)
        raw_text = pdf_service.extract_text(file_path)

        # 2. Render Page (For Tier 2 Fallback)
        image_bytes = pdf_service.render_page_to_image(file_path, 0)

        # 3. AI Extraction via Cascade
        metadata, tier = await ai_service.process(
            text=raw_text, image_bytes=image_bytes
        )

        # 4. Local Normalization
        standardized_company = normalizer.normalize(metadata.company_name)

        # 5. Create New Filename
        new_filename = f"{standardized_company} PO{metadata.po_number} INV{metadata.invoice_number}.pdf"

        # 6. Physical Split
        output_paths = pdf_service.split_pdf(
            source_path=file_path, page_ranges=[[0]], output_names=[new_filename]
        )

        # 7. Save to Database
        new_invoice = Invoice(
            job_id=job.id,
            company_name=standardized_company,
            po_number=metadata.po_number,
            invoice_number=metadata.invoice_number,
            tier_used=tier,
            raw_text=raw_text,
            confidence_score=metadata.confidence,
            original_split_path=str(output_paths[0]),
        )
        db.add(new_invoice)

        job.status = JobStatus.COMPLETED
        db.add(job)
        db.commit()
        logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        job.status = JobStatus.FAILED
        job.error_message = str(e)
        db.add(job)
        db.commit()


@app.post("/upload/")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    """Receives a PDF, saves it, and starts a background processing job."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_filename = f"{uuid.uuid4()}_{file.filename}"
    save_path = settings.UPLOAD_DIR / temp_filename

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    job = Job(filename=file.filename, status=JobStatus.PENDING)
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(process_pdf_task, job.id, save_path, db)

    return {"job_id": job.id, "status": "queued", "filename": file.filename}


@app.get("/jobs/")
async def list_jobs(db: Session = Depends(get_session)):
    """Returns the 20 most recent jobs."""
    from sqlmodel import select

    statement = select(Job).order_by(desc(Job.id)).limit(20)
    results = db.exec(statement).all()
    return results


@app.get("/jobs/{job_id}")
async def get_job_status(job_id: int, db: Session = Depends(get_session)):
    """Check the status of a specific processing job."""
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return {
        "id": job.id,
        "status": job.status,
        "created_at": job.created_at,
        "invoices": job.invoices,
        "error": job.error_message,
    }


@app.get("/health")
async def health_check():
    return {"status": "online", "app": settings.APP_NAME}


# Mount static files correctly
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# Serve the UI
@app.get("/")
async def serve_ui():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)
