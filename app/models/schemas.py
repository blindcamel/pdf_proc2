from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TierUsed(str, Enum):
    TIER_1 = "text_only"
    TIER_2 = "vision_fallback"

class Job(SQLModel, table=True):
    """Tracks a single upload/processing session"""
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    status: JobStatus = Field(default=JobStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    
    # Relationship to invoices found within this job
    invoices: List["Invoice"] = Relationship(back_populates="job")

class Invoice(SQLModel, table=True):
    """Stores the extracted metadata for a single invoice"""
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    
    # Extracted Data
    company_name: str
    po_number: str
    invoice_number: str
    
    # Processing Metadata
    tier_used: TierUsed
    raw_text: Optional[str] = None
    confidence_score: float = 0.0
    
    # File Paths
    original_split_path: str  # Where the specific split PDF lives
    
    job: Job = Relationship(back_populates="invoices")

class InvoiceMetadata(SQLModel):
    """
    This is the 'Structured Output' schema we give to the AI.
    The AI must return exactly this format.
    """
    company_name: str = Field(description="The standardized name of the company")
    po_number: str = Field(description="The Purchase Order number")
    invoice_number: str = Field(description="The Invoice identifier")
    confidence: float = Field(description="Score between 0 and 1 of how certain the extraction is")