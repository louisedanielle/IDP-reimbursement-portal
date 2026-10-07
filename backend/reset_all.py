"""
Full reset - clears database, uploads, outputs, processed files, and Redis queue.
Run with: python reset_all.py
"""
import os
import shutil
import redis
from pathlib import Path

from app.config import settings
from app.database import engine, SessionLocal
from app.models import Base, Document, ExtractedData, Reimbursement, ReimbursementLineItem


def reset_database():
    """Drop and recreate all tables"""
    print("🗑️  Dropping database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Creating fresh tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database reset complete")


def reset_folders():
    """Delete and recreate content folders"""
    folders = [
        settings.UPLOAD_DIR,
        settings.OUTPUT_DIR,
        "./watch_folder/processed",
        "./watch_folder/failed",
    ]
    
    for folder in folders:
        path = Path(folder)
        if path.exists():
            print(f"🗑️  Clearing {folder}...")
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            print(f"✅ Cleared {folder}")
        else:
            path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created {folder}")


def reset_redis():
    """Flush the Redis queue (removes any pending Celery tasks)"""
    try:
        print("🗑️  Clearing Redis queue...")
        r = redis.from_url(settings.REDIS_URL)
        r.flushall()
        print("✅ Redis cleared")
    except Exception as e:
        print(f"⚠️  Could not clear Redis: {e}")


def main():
    print("=" * 60)
    print("🔄 FULL RESET - Clearing all uploaded data")
    print("=" * 60)
    
    # Confirm
    confirm = input("\n⚠️  This will delete ALL data. Type 'yes' to continue: ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print()
    reset_database()
    print()
    reset_folders()
    print()
    reset_redis()
    
    print()
    print("=" * 60)
    print("✅ FULL RESET COMPLETE")
    print("=" * 60)
    print("You can now start fresh by uploading new receipts.")


if __name__ == "__main__":
    main()