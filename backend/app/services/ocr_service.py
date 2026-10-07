import os
import base64
import json
from typing import Dict, Any, Optional
from pathlib import Path
import pytesseract
from PIL import Image
import io

from ..config import settings

class OCRService:
    def __init__(self):
        self.provider = self._detect_provider()
        
    def _detect_provider(self) -> str:
        """Auto-detect which OCR provider to use"""
        if settings.GOOGLE_APPLICATION_CREDENTIALS and settings.DOCUMENT_AI_PROJECT_ID:
            return "google"
        elif settings.AZURE_ENDPOINT and settings.AZURE_API_KEY:
            return "azure"
        else:
            return "tesseract"  # Fallback to open-source
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image using the configured provider"""
        if self.provider == "google":
            return self._extract_google(image_path)
        elif self.provider == "azure":
            return self._extract_azure(image_path)
        else:
            return self._extract_tesseract(image_path)
    
    def _extract_google(self, image_path: str) -> Dict[str, Any]:
        """Extract using Google Document AI"""
        try:
            from google.cloud import documentai_v1 as documentai
            
            # Initialize client
            client = documentai.DocumentProcessorServiceClient()
            
            # Read image
            with open(image_path, "rb") as image_file:
                image_content = image_file.read()
            
            # Configure process request
            name = client.processor_path(
                settings.DOCUMENT_AI_PROJECT_ID,
                settings.DOCUMENT_AI_LOCATION,
                settings.DOCUMENT_AI_PROCESSOR_ID
            )
            
            document = {"content": image_content, "mime_type": "image/jpeg"}
            request = {"name": name, "raw_document": document}
            
            # Process document
            result = client.process_document(request=request)
            document = result.document
            
            # Extract fields
            extracted_data = {
                "raw_text": document.text,
                "entities": [],
                "confidence": 0.0
            }
            
            # Parse entities if using custom processor
            if hasattr(document, 'entities'):
                for entity in document.entities:
                    extracted_data["entities"].append({
                        "type": entity.type_,
                        "value": entity.mention_text,
                        "confidence": entity.confidence
                    })
                if extracted_data["entities"]:
                    extracted_data["confidence"] = sum(
                        e["confidence"] for e in extracted_data["entities"]
                    ) / len(extracted_data["entities"])
            
            return extracted_data
            
        except ImportError:
            # Fallback to tesseract if Google client not installed
            return self._extract_tesseract(image_path)
        except Exception as e:
            raise Exception(f"Google Document AI extraction failed: {str(e)}")
    
    def _extract_azure(self, image_path: str) -> Dict[str, Any]:
        """Extract using Azure Document Intelligence"""
        try:
            from azure.ai.documentintelligence import DocumentIntelligenceClient
            from azure.core.credentials import AzureKeyCredential
            
            # Initialize client
            client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_API_KEY)
            )
            
            # Read image
            with open(image_path, "rb") as image_file:
                image_content = image_file.read()
            
            # Analyze document
            poller = client.begin_analyze_document(
                settings.AZURE_MODEL_ID or "prebuilt-layout",
                document=image_content
            )
            result = poller.result()
            
            extracted_data = {
                "raw_text": "",
                "entities": [],
                "confidence": 0.0
            }
            
            # Extract text
            if result.content:
                extracted_data["raw_text"] = result.content
            
            # Extract key-value pairs from documents
            if hasattr(result, 'documents') and result.documents:
                for doc in result.documents:
                    if hasattr(doc, 'fields'):
                        for field_name, field_value in doc.fields.items():
                            extracted_data["entities"].append({
                                "type": field_name,
                                "value": field_value.content if hasattr(field_value, 'content') else str(field_value),
                                "confidence": field_value.confidence if hasattr(field_value, 'confidence') else 0.0
                            })
            
            return extracted_data
            
        except ImportError:
            return self._extract_tesseract(image_path)
        except Exception as e:
            raise Exception(f"Azure Document Intelligence extraction failed: {str(e)}")
    
    def _extract_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Extract using Tesseract OCR (open-source fallback)"""
        try:
            # Open image
            image = Image.open(image_path)
            
            # Extract text with Tesseract
            raw_text = pytesseract.image_to_string(
                image,
                lang='eng+chi_sim',  # English + Simplified Chinese
                config='--psm 6'  # Assume single block of text
            )
            
            return {
                "raw_text": raw_text,
                "entities": [],
                "confidence": 0.8  # Default confidence for Tesseract
            }
            
        except Exception as e:
            raise Exception(f"Tesseract OCR extraction failed: {str(e)}")