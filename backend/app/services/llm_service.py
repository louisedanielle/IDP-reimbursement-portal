import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from ..config import settings

class LLMService:
    def __init__(self):
        self.provider = self._detect_provider()
        self.client = None
        self._initialize_client()
    
    def _detect_provider(self) -> str:
        """Detect which LLM provider to use"""
        if settings.OPENAI_API_KEY:
            return "openai"
        else:
            return "fallback"
    
    def _initialize_client(self):
        """Initialize the appropriate client"""
        if self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            except ImportError:
                self.provider = "fallback"
    
    def parse_expense_receipt(self, ocr_text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Parse OCR text into structured expense items using LLM"""
        if self.provider == "openai" and self.client:
            return self._parse_with_openai(ocr_text, context)
        else:
            return self._parse_with_fallback(ocr_text)
    
    def _parse_with_openai(self, ocr_text: str, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Parse using OpenAI GPT"""
        try:
            prompt = self._build_prompt(ocr_text, context)
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": """You are an expense receipt parser. Extract line items from the receipt text.
                    Return a JSON array where each item has: date, description, amount_hkd.
                    If the amount is in RMB, convert to HKD using 1 RMB = 1.15 HKD."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            # Extract items from response
            items = result.get("items", [])
            
            # Add confidence and categorize
            for i, item in enumerate(items):
                item["item_number"] = i + 1
                item["confidence"] = 0.85
                item["category"] = self._categorize_item(item.get("description", ""))
                
                # Ensure amount is float
                if "amount_hkd" in item:
                    item["amount_hkd"] = float(item["amount_hkd"])
            
            return items
            
        except Exception as e:
            print(f"OpenAI parsing failed: {str(e)}")
            return self._parse_with_fallback(ocr_text)
    
    def _parse_with_fallback(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Fallback parsing without LLM"""
        # Use simple pattern matching
        items = []
        lines = ocr_text.split('\n')
        
        # Patterns
        date_pattern = r'(\d{4}[-/]\d{2}[-/]\d{2})|(\d{2}[-/]\d{2}[-/]\d{4})'
        amount_pattern = r'(?:HKD|HK\$|港币|RMB|¥|￥)\s*([\d,]+\.?\d*)|([\d,]+\.?\d*)\s*(?:HKD|HK\$)'
        
        current_item = {}
        item_number = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            date_match = re.search(date_pattern, line)
            amount_match = re.search(amount_pattern, line)
            
            if date_match and amount_match:
                if current_item and "date" in current_item:
                    items.append(current_item)
                    item_number += 1
                
                current_item = {
                    "item_number": item_number,
                    "date": date_match.group(0),
                    "description": line,
                    "amount_hkd": float(re.sub(r'[^\d\.]', '', amount_match.group(0) or amount_match.group(1) or "0")),
                    "confidence": 0.6,
                    "category": self._categorize_item(line)
                }
            elif current_item and "date" in current_item:
                current_item["description"] += " " + line
        
        if current_item and "date" in current_item:
            items.append(current_item)
        
        return items
    
    def _build_prompt(self, ocr_text: str, context: Optional[Dict] = None) -> str:
        """Build the prompt for LLM"""
        prompt = f"""Extract expense items from the following receipt text:

{ocr_text}

Return a JSON object with an 'items' array. Each item should have:
- date: The date of the expense (YYYY-MM-DD format)
- description: Description of the expense
- amount_hkd: The amount in HKD (if in RMB, convert using 1 RMB = 1.15 HKD)

Example output:
{{"items": [
    {{"date": "2026-06-01", "description": "Hotel stay", "amount_hkd": 6076.32}},
    {{"date": "2026-06-02", "description": "Dinner with client", "amount_hkd": 4026.12}}
]}}
"""
        
        if context:
            prompt += f"\n\nContext: {json.dumps(context)}"
        
        return prompt
    
    def _categorize_item(self, description: str) -> str:
        """Categorize expense item"""
        categories = {
            "Hotel": ["hotel", "marriott", "hilton", "stay", "night", "lodging", "住宿"],
            "Transportation": ["air ticket", "flight", "train", "hsr", "taxi", "cab", "打車", "高铁", "机票"],
            "Meals": ["lunch", "dinner", "breakfast", "meal", "restaurant", "drink", "tea", "coffee", "吃饭", "茶"],
            "Entertainment": ["gift", "present", "entertainment", "礼物", "娱乐"]
        }
        
        desc_lower = description.lower()
        for category, keywords in categories.items():
            if any(keyword in desc_lower for keyword in keywords):
                return category
        
        return "Other"