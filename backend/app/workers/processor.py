import asyncio
import os
from uuid import UUID
from datetime import datetime

from celery import Celery

from ..config import settings
from ..database import SessionLocal
from ..models import Document, ExtractedData
from ..services.grok_service import GrokService


app = Celery(
    'processor',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    broker_connection_retry_on_startup=True,
)

grok_service = GrokService()


@app.task(
    name='app.workers.processor.process_document',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 2, 'countdown': 5},
)
def process_document(self, document_id: str):
    """Extract line items from an uploaded document using Grok."""
    db = SessionLocal()
    document = None
    tmp_path = None

    try:
        try:
            doc_uuid = UUID(str(document_id))
        except (ValueError, AttributeError, TypeError):
            return {"status": "failed", "message": "Invalid document_id"}

        document = db.query(Document).filter(Document.id == doc_uuid).first()
        if not document:
            return {"status": "failed", "message": "Document not found"}

        document.status = "processing"
        db.commit()
        print(f"🔄 Processing: {document.filename}")

        # --- Write file bytes to a temp file on the worker's disk ---
        if document.file_data:
            import tempfile
            suffix = os.path.splitext(document.filename)[1] or ".jpg"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(document.file_data)
            tmp.close()
            tmp_path = tmp.name
        elif document.file_path and os.path.exists(document.file_path):
            tmp_path = document.file_path
        else:
            print("❌ No file data available on Document record")
            document.status = "failed"
            document.error_message = "No file data"
            db.commit()
            return {"status": "failed", "message": "No file data"}

        # --- Extract with Grok ---
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                grok_service.extract_receipt_data(tmp_path)
            )
        finally:
            loop.close()

        items = result.get("items", [])
        payee_name = result.get("payee_name")
        document_type = result.get("document_type", "other")
        total_amount = result.get("total_amount")

        print(
            f"✅ Extracted {len(items)} items | payee: {payee_name} | "
            f"type: {document_type} | total: {total_amount}"
        )

        # --- Save extracted data ---
        extracted = ExtractedData(
            document_id=document.id,
            raw_text=result.get("raw_text", ""),
            structured_data={
                "items": items,
                "payee_name": payee_name,
                "document_type": document_type,
                "total_amount": total_amount,
            },
            confidence_score=result.get("confidence", 0.0),
        )
        db.add(extracted)
        document.status = "completed"
        db.commit()

        return {
            "status": "success",
            "document_id": str(document.id),
            "items_count": len(items),
            "payee_name": payee_name,
            "document_type": document_type,
            "total_amount": total_amount,
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        if document:
            document.status = "failed"
            document.error_message = str(e)
            db.commit()
        return {"status": "failed", "message": str(e)}

    finally:
        # Clean up the temp file
        if tmp_path and document and tmp_path != getattr(document, "file_path", None):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        db.close()