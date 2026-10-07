from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import json

from ..database import get_db
from ..models import Reimbursement, ReimbursementLineItem, Document, ExtractedData, Correction, TrainingData
from ..schemas import *
from ..services.excel_generator import ExcelGenerator
from ..services.pdf_generator import PDFGenerator

router = APIRouter()
excel_generator = ExcelGenerator()
pdf_generator = PDFGenerator()

@router.get("/", response_model=List[ReimbursementResponse])
async def list_reimbursements(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all reimbursements"""
    query = db.query(Reimbursement)
    
    if status:
        query = query.filter(Reimbursement.status == status)
    
    reimbursements = query.order_by(
        Reimbursement.created_date.desc()
    ).offset(skip).limit(limit).all()
    
    return [reimb.to_dict() for reimb in reimbursements]

@router.get("/{reimbursement_id}", response_model=ReimbursementResponse)
async def get_reimbursement(
    reimbursement_id: UUID,
    db: Session = Depends(get_db)
):
    """Get reimbursement by ID"""
    reimbursement = db.query(Reimbursement).filter(
        Reimbursement.id == reimbursement_id
    ).first()
    
    if not reimbursement:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    
    return reimbursement

@router.post("/", response_model=ReimbursementResponse)
async def create_reimbursement(
    data: ReimbursementCreate,
    db: Session = Depends(get_db)
):
    """Create a new reimbursement"""
    # Generate PR number
    year = datetime.utcnow().year
    last_pr = db.query(Reimbursement).order_by(
        Reimbursement.created_date.desc()
    ).first()
    
    if last_pr:
        parts = last_pr.pr_number.split('-')
        if len(parts) >= 4:
            try:
                last_num = int(parts[-1])
                next_num = last_num + 1
            except:
                next_num = 1
        else:
            next_num = 1
    else:
        next_num = 1
    
    pr_number = f"LSI-PR-{year}-{next_num:03d}"
    
    # Calculate total
    total_amount = sum(item.amount_hkd for item in data.line_items)
    
    # Create reimbursement
    reimbursement = Reimbursement(
        pr_number=pr_number,
        applicant=data.applicant,
        payee_name=data.payee_name,
        nature=data.nature,
        total_amount=total_amount,
        status="draft"
    )
    db.add(reimbursement)
    db.commit()
    db.refresh(reimbursement)
    
    # Create line items
    for item_data in data.line_items:
        line_item = ReimbursementLineItem(
            reimbursement_id=reimbursement.id,
            item_number=item_data.item_number,
            date=item_data.date,
            description=item_data.description,
            amount_hkd=item_data.amount_hkd,
            category=item_data.category
        )
        db.add(line_item)
    db.commit()
    
    return reimbursement

@router.put("/{reimbursement_id}", response_model=ReimbursementResponse)
async def update_reimbursement(
    reimbursement_id: UUID,
    data: ReimbursementUpdate,
    db: Session = Depends(get_db)
):
    """Update reimbursement"""
    reimbursement = db.query(Reimbursement).filter(
        Reimbursement.id == reimbursement_id
    ).first()
    
    if not reimbursement:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    
    # Update fields
    if data.applicant:
        reimbursement.applicant = data.applicant
    if data.payee_name:
        reimbursement.payee_name = data.payee_name
    if data.nature:
        reimbursement.nature = data.nature
    
    # Update line items if provided
    if data.line_items is not None:
        # Delete existing line items
        db.query(ReimbursementLineItem).filter(
            ReimbursementLineItem.reimbursement_id == reimbursement_id
        ).delete()
        
        # Create new line items
        for item_data in data.line_items:
            line_item = ReimbursementLineItem(
                reimbursement_id=reimbursement.id,
                item_number=item_data.item_number,
                date=item_data.date,
                description=item_data.description,
                amount_hkd=item_data.amount_hkd,
                category=item_data.category
            )
            db.add(line_item)
        
        # Update total
        reimbursement.total_amount = sum(item.amount_hkd for item in data.line_items)
    
    db.commit()
    db.refresh(reimbursement)
    
    return reimbursement

@router.post("/{reimbursement_id}/approve")
async def approve_reimbursement(
    reimbursement_id: UUID,
    action: ApprovalAction,
    db: Session = Depends(get_db)
):
    """Approve or reject reimbursement"""
    reimbursement = db.query(Reimbursement).filter(
        Reimbursement.id == reimbursement_id
    ).first()
    
    if not reimbursement:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    
    # Update status
    if action.action == "submitted":
        reimbursement.status = "submitted"
        reimbursement.submitted_date = datetime.utcnow()
    elif action.action == "approved":
        reimbursement.status = "approved"
        reimbursement.approved_date = datetime.utcnow()
    elif action.action == "rejected":
        reimbursement.status = "rejected"
    elif action.action == "paid":
        reimbursement.status = "paid"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    # Record approval history
    from ..models import ApprovalHistory
    history = ApprovalHistory(
        reimbursement_id=reimbursement.id,
        action=action.action,
        action_by=action.action_by,
        comments=action.comments
    )
    db.add(history)
    db.commit()
    
    # If approved, generate final documents
    if action.action == "approved":
        # Generate Excel
        line_items = db.query(ReimbursementLineItem).filter(
            ReimbursementLineItem.reimbursement_id == reimbursement_id
        ).all()
        
        items = [{
            "date": item.date,
            "description": item.description,
            "amount_hkd": item.amount_hkd,
            "category": item.category
        } for item in line_items]
        
        data = {
            "pr_number": reimbursement.pr_number,
            "applicant": reimbursement.applicant,
            "payee_name": reimbursement.payee_name,
            "nature": reimbursement.nature,
            "line_items": items
        }
        
        excel_path = excel_generator.generate_reimbursement_excel(data)
        
        return {
            "message": "Reimbursement approved successfully",
            "pr_number": reimbursement.pr_number,
            "status": reimbursement.status,
            "excel_path": excel_path
        }
    
    return {
        "message": f"Reimbursement {action.action} successfully",
        "pr_number": reimbursement.pr_number,
        "status": reimbursement.status
    }

@router.get("/{reimbursement_id}/export/excel")
async def export_reimbursement_excel(
    reimbursement_id: UUID,
    db: Session = Depends(get_db)
):
    """Export reimbursement as Excel file"""
    reimbursement = db.query(Reimbursement).filter(
        Reimbursement.id == reimbursement_id
    ).first()
    
    if not reimbursement:
        raise HTTPException(status_code=404, detail="Reimbursement not found")
    
    line_items = db.query(ReimbursementLineItem).filter(
        ReimbursementLineItem.reimbursement_id == reimbursement_id
    ).all()
    
    items = [{
        "date": item.date,
        "description": item.description,
        "amount_hkd": item.amount_hkd,
        "category": item.category
    } for item in line_items]
    
    data = {
        "pr_number": reimbursement.pr_number,
        "applicant": reimbursement.applicant,
        "payee_name": reimbursement.payee_name,
        "nature": reimbursement.nature,
        "line_items": items
    }
    
    excel_path = excel_generator.generate_reimbursement_excel(data)
    
    from fastapi.responses import FileResponse
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{reimbursement.pr_number}.xlsx"
    )