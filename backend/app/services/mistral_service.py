import base64
import json
import re
from typing import List, Dict, Any
from datetime import datetime

from mistralai import Mistral

from ..config import settings


EXPENSE_CATEGORIES = [
    {"name": "Drinks & Meals With Clients",
     "description": "Food and beverages bought during work trips or business meetings."},
    {"name": "Entertainment",
     "description": "Gift to Client, leisure and entertainment activities with clients."},
    {"name": "Hotel",
     "description": "Hotel for Business Trip."},
    {"name": "Office Equipment & Supplies",
     "description": "Pens, paper, cables, shredder, chairs, computers, office furniture."},
    {"name": "Research and Development Expenses",
     "description": "AI / GPT API Fee."},
    {"name": "Sundry Expenses",
     "description": "Small office items, keys, plants, cleaning supplies, water deposit."},
    {"name": "Transportation",
     "description": "MTR, Octopus, Taxi, Uber, Air Ticket, High-speed rail (HSR)."},
    {"name": "Travel Expenses",
     "description": "Visa fees, passport renewal, international vaccination certificates."},
]


class MistralService:
    def __init__(self):
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        self.vision_model = settings.MISTRAL_VISION_MODEL
        self.categories = EXPENSE_CATEGORIES

    async def extract_receipt_data(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            mime_type = self._get_mime_type(image_path)
            return await self._extract_with_vision(image_base64, mime_type)
        except Exception as e:
            print(f"❌ Mistral extraction error: {e}")
            return {
                "raw_text": "",
                "payee_name": None,
                "document_type": "other",
                "total_amount": None,
                "items": [],
                "confidence": 0.0,
                "error": str(e),
            }

    async def _extract_with_vision(self, image_base64, mime_type):
        category_lines = "\n".join(
            f"{i}. {c['name']} — {c['description']}"
            for i, c in enumerate(self.categories, 1)
        )
        category_names = ", ".join(f'"{c["name"]}"' for c in self.categories)

        system_prompt = f"""You are a financial document extraction assistant.
Your task is to extract structured data from financial documents
(receipts, bills, invoices, statements, cheques, salary slips).

CRITICAL RULES:

1. READ THE IMAGE — do NOT hallucinate. If a value isn't on the document,
   return null.

2. RAW TEXT — return the full text you see on the document as a single
   string, preserving line breaks.

3. PAYEE NAME — the person or ORGANIZATION the payment is FOR. This is
   usually the MERCHANT or VENDOR, not a contact person or employee.
   Priority:
     a) The company the bill/invoice is issued BY
     b) The merchant name on a receipt
     c) The employee (for reimbursements, MPF, or salary)
   Return the name EXACTLY as printed. If none is visible, return null.

4. TRANSACTION DATE — the date the transaction occurred. Format: "YYYY-MM-DD".

5. TOTAL AMOUNT — very important. Look for a line that says one of:
   - "Total", "Total Amount", "Total Amount Due", "Grand Total",
     "Amount Due", "Amount Payable", "Balance Due", "Net Amount",
     "Amount to Pay", "Pay This Amount"
   - Chinese: 總額, 总额, 合計, 合计, 應付, 应付, 金額, 金额
   Extract that line's amount as "total_amount" (a number in HKD).

   If the document has NO explicit total line, set "total_amount" to null.

6. LINE ITEMS — extract EVERY financial line from the document, INCLUDING
   the total line. For each item, set "is_total" to true if that specific
   line is the total/amount-due row, otherwise false.

   This lets downstream code sum the breakdown separately from the total.

7. AMOUNT — for each line item, use the amount printed (in HKD; convert
   if needed).

8. DESCRIPTION — clear English description under 200 chars.

9. CATEGORY — pick ONE (for reimbursements only):
{category_lines}

10. LANGUAGE — documents may be English, Chinese, or mixed.

11. DOCUMENT TYPE — one of: bill, receipt, mpf, cheque, invoice,
    salary, insurance, other.

OUTPUT — return ONLY valid JSON:
{{
  "raw_text": "the full text read from the document",
  "payee_name": "the merchant/vendor/payee name, or null",
  "document_type": "bill | receipt | mpf | cheque | invoice | salary | insurance | other",
  "total_amount": 0.00,
  "items": [
    {{
      "date": "YYYY-MM-DD",
      "description": "string",
      "amount_hkd": 0.00,
      "category": "one of: {category_names}",
      "is_total": false
    }}
  ]
}}"""

        user_prompt = """Read this document and return:
1. raw_text — the full text you see
2. payee_name — the merchant/vendor/payee the payment is FOR
3. document_type — bill, receipt, mpf, cheque, invoice, salary, insurance, or other
4. total_amount — the amount on the "Total" / "Amount Due" line, or null
5. items — every financial line, each marked with is_total: true if it's the total row

Return JSON only."""

        try:
            response = self.client.chat.complete(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                },
                            },
                        ],
                    },
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            payee_name = result.get("payee_name")
            if isinstance(payee_name, str):
                payee_name = payee_name.strip() or None

            raw_text = result.get("raw_text") or ""
            if isinstance(raw_text, str):
                raw_text = raw_text.strip()

            total_amount = result.get("total_amount")
            if total_amount is not None:
                total_amount = self._normalize_amount(total_amount)
            else:
                total_amount = None

            items = result.get("items", [])
            formatted_items = []
            for idx, item in enumerate(items):
                category = self._normalize_category(item.get("category"))
                formatted_items.append({
                    "item_number": idx + 1,
                    "date": self._normalize_date(item.get("date")),
                    "description": (item.get("description") or "").strip(),
                    "amount_hkd": self._normalize_amount(item.get("amount_hkd")),
                    "category": category,
                    "is_total": bool(item.get("is_total", False)),
                    "confidence": 0.85,
                })

            return {
                "raw_text": raw_text,
                "payee_name": payee_name,
                "document_type": result.get("document_type") or "other",
                "total_amount": total_amount,
                "items": formatted_items,
                "confidence": 0.85,
                "model": self.vision_model,
            }

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return {
                "raw_text": "", "payee_name": None, "document_type": "other",
                "total_amount": None, "items": [], "confidence": 0.0,
            }
        except Exception as e:
            print(f"❌ Vision extraction error: {e}")
            return {
                "raw_text": "", "payee_name": None, "document_type": "other",
                "total_amount": None, "items": [], "confidence": 0.0,
            }

    def _normalize_category(self, value):
        if not value or not isinstance(value, str):
            return None
        needle = value.strip().lower()
        for c in self.categories:
            if c["name"].lower() == needle:
                return c["name"]
        return None

    def _normalize_date(self, value):
        if not value or not isinstance(value, str):
            return ""
        s = value.strip()
        iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
        if iso:
            return f"{iso.group(1)}-{iso.group(2)}-{iso.group(3)}"
        for fmt in (
            "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y.%m.%d",
            "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
        ):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        frag = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
        if frag:
            y, m, d = frag.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"
        return s

    def _normalize_amount(self, value):
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return round(float(value), 2)
        try:
            cleaned = "".join(c for c in str(value) if c.isdigit() or c in ".-")
            return round(float(cleaned or 0), 2)
        except (ValueError, TypeError):
            return 0.0

    def _get_mime_type(self, file_path):
        ext = file_path.lower().split(".")[-1]
        return {
            "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
            "tiff": "image/tiff", "tif": "image/tiff", "pdf": "application/pdf",
        }.get(ext, "image/jpeg")