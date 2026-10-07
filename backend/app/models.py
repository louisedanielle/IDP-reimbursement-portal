from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, JSON,
    Text, Boolean, Uuid, LargeBinary,   
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from .database import Base


# ============ LOOKUP TABLES ============

class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)    
    file_data = Column(LargeBinary, nullable=True)    
    file_size = Column(Integer)
    mime_type = Column(String(100))
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False)


class PaymentType(Base):
    __tablename__ = "payment_types"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False)

    categories = relationship("PaymentCategory", back_populates="payment_type")


class PaymentCategory(Base):
    __tablename__ = "payment_categories"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=False)
    payment_type_id = Column(Uuid, ForeignKey("payment_types.id"), nullable=False)
    name = Column(String(100), nullable=False)
    frequency = Column(String(20), nullable=False)   # "monthly" | "annual" | "adhoc"
    is_active = Column(Boolean, default=True)

    company = relationship("Company", back_populates="categories")
    payment_type = relationship("PaymentType", back_populates="categories")


class Payee(Base):
    __tablename__ = "payees"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False)
    payee_type = Column(String(50), default="staff")   # "staff" | "vendor" | "other"
    email = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)


# ============ CORE TABLES ============

class Document(Base):
    __tablename__ = "documents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="pending")
    error_message = Column(Text, nullable=True)

    extracted_data = relationship(
        "ExtractedData", back_populates="document", uselist=False
    )


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id = Column(Uuid, ForeignKey("documents.id"), nullable=False)
    raw_text = Column(Text, nullable=True)
    structured_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    extraction_date = Column(DateTime, default=datetime.utcnow)
    is_verified = Column(Boolean, default=False)

    document = relationship("Document", back_populates="extracted_data")


class Requisition(Base):
    """
    A Payment Requisition (PR).

    One PR = one (company, category, payee, period).
    For reimbursements, period is a month (YYYY-MM) and all line items
    for that payee + month roll up into this single PR.
    """
    __tablename__ = "requisitions"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    pr_number = Column(String(80), unique=True, nullable=False)

    company_id = Column(Uuid, ForeignKey("companies.id"), nullable=True)
    payment_category_id = Column(
        Uuid, ForeignKey("payment_categories.id"), nullable=True
    )
    payee_id = Column(Uuid, ForeignKey("payees.id"), nullable=True)

    # Denormalized names for fast display without joins
    company_name = Column(String(200), nullable=True)
    category_name = Column(String(100), nullable=True)
    payment_type_name = Column(String(50), nullable=True)
    payee_name = Column(String(200), nullable=False)

    applicant = Column(String(100), default="Juliana")
    nature = Column(String(50), default="Payment Requisition")

    period = Column(String(20), nullable=True)         # "2026-06" | "2026" | "2026-06-15"
    frequency = Column(String(20), nullable=True)      # "monthly" | "annual" | "adhoc"

    total_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="HKD")
    status = Column(String(50), default="draft")       # draft | approved | paid

    created_date = Column(DateTime, default=datetime.utcnow)
    submitted_date = Column(DateTime, nullable=True)
    approved_date = Column(DateTime, nullable=True)

    line_items = relationship(
        "LineItem",
        back_populates="requisition",
        cascade="all, delete-orphan",
    )


class LineItem(Base):
    """
    A single expense or payment line inside a PR.
    For reimbursements, `category` is the reimbursement category
    (Hotel, Transportation, Drinks & Meals With Clients, etc.).
    For other payment types, `category` is usually null.
    """
    __tablename__ = "line_items"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    requisition_id = Column(
        Uuid, ForeignKey("requisitions.id"), nullable=False
    )
    source_document_id = Column(
        Uuid, ForeignKey("documents.id"), nullable=True
    )

    item_number = Column(Integer, nullable=False)   # 1, 2, 3... within the PR

    date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    amount_hkd = Column(Float, nullable=False)

    # Reimbursement category (Hotel, Transportation, etc.)
    category = Column(String(100), nullable=True)

    # Free-form extra fields (e.g. MPF employer/employee split)
    meta = Column(JSON, nullable=True)

    requisition = relationship("Requisition", back_populates="line_items")