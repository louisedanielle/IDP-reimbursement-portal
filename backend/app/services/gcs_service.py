import os
from typing import Optional, BinaryIO
from io import BytesIO
from google.cloud import storage
from google.cloud.storage import Blob
from ..config import settings

class GCSService:
    """Google Cloud Storage service for handling file uploads and downloads"""
    
    def __init__(self):
        self.client = storage.Client(project=settings.GCP_PROJECT_ID)
        self.bucket_name = settings.GCS_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if not"""
        try:
            self.client.get_bucket(self.bucket_name)
        except Exception:
            if settings.APP_ENV != "development":
                bucket = self.client.create_bucket(
                    self.bucket_name,
                    location="US"
                )
                print(f"Created bucket: {self.bucket_name}")
    
    def upload_file(self, file_data: bytes, destination_path: str, content_type: Optional[str] = None) -> str:
        """Upload a file to GCS"""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(destination_path)
        
        blob.upload_from_string(
            file_data,
            content_type=content_type
        )
        
        return f"gs://{self.bucket_name}/{destination_path}"
    
    def upload_from_file(self, local_path: str, destination_path: str) -> str:
        """Upload a file from local path to GCS"""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(destination_path)
        
        with open(local_path, 'rb') as f:
            blob.upload_from_file(f)
        
        return f"gs://{self.bucket_name}/{destination_path}"
    
    def download_file(self, source_path: str, destination_path: str) -> str:
        """Download a file from GCS to local path"""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(source_path)
        blob.download_to_filename(destination_path)
        return destination_path
    
    def get_file_url(self, path: str) -> str:
        """Get public URL for a file"""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(path)
        return blob.public_url
    
    def list_files(self, prefix: str = "") -> list:
        """List files in the bucket"""
        bucket = self.client.bucket(self.bucket_name)
        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    
    def delete_file(self, path: str) -> bool:
        """Delete a file from GCS"""
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(path)
        blob.delete()
        return True