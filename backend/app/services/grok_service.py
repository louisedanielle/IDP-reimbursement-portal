import base64
import json
import re
from typing import List, Dict, Any
from datetime import datetime

from openai import OpenAI

from ..config import settings


# ============================================================
# Reimbursement categories — from the official Leapstack list
# ============================================================
EXPENSE_CATEGORIES = [
    {
        "name": "Drinks & Meals With Clients",
        "description": (
            "Food and beverages bought during work trips or business meetings."
        ),
    },
    {
        "name": "Entertainment",
        "description": (
            "Gift to Client, leisure and entertainment activities undertaken "
            "with clients, with the aim of establishing or maintaining business "
            "relationships."
        ),
    },
    {
        "name": "Hotel",
        "description": "Hotel for Business Trip.",
    },
    {
        "name": "Office Equipment & Supplies",
        "description": (
            "Writing and desktop tools (pens, highlighters, scissors, staplers, "
            "tape, sticky notes); paper and printing supplies (A4, notebooks, "
            "envelopes, labels, toner, ink); document management (folders, "
            "file dividers, hole punch); computer peripherals (mouse, keyboard, "
            "USB drive, extension cable, network cable); small appliances (paper "
            "shredder, label maker, cleaning machine, desktop fan); technology "
            "and electronics (computers, laptops, servers, photocopiers, "
            "projectors, company smartphones); office furniture (desks, chairs, "
            "conference tables, filing cabinets, sofas)."
        ),
    },
    {
        "name": "Research and Development Expenses",
        "description": "AI / GPT API Fee.",
    },
    {
        "name": "Sundry Expenses",
        "description": (
            "Office incidentals such as keys and locks (making keys, changing "
            "locks, locker padlocks); small cleaning supplies (rags, garbage "
            "bags, pesticides) not covered by regular cleaning contracts; "
            "decorations and greenery (potted plants, temporary holiday "
            "decorations); water dispenser bucket deposit."
        ),
    },
    {
        "name": "Transportation",
        "description": (
            "MTR, Octopus, Taxi, Uber, Air Ticket, High-speed rail (HSR)."
        ),
    },
    {
        "name": "Travel Expenses",
        "description": (
            "Necessary expenses incurred to facilitate business operations in "
            "a different location: visa fees for the destination country, "
            "passport application/renewal fees, international vaccination "
            "certificate fees."
        ),
    },
]


class GrokService:
    """
    Extracts structured expense data from receipt images using xAI's Grok
    vision model (OpenAI-compatible API).

    Returns:
        {
          "payee_name": str | None,
          "items": [...],
          "confidence": float,
          "model": str,
        }
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.XAI_API_KEY,
            base_url="https://api.x.ai/v1",
        )
        self.vision_model = settings.XAI_VISION_MODEL
        self.categories = EXPENSE_CATEGORIES

    async def extract_receipt_data(self, image_path: str) -> Dict[str, Any]:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            mime_type = self._get_mime_type(image_path)
            return await self._extract_with_vision(image_base64, mime_type)
        except Exception as e:
            print(f"❌ Grok extraction error: {e}")
            return {
                "payee_name": None,
                "document_type": "other",
                "total_amount": None,
                "items": [],
                "confidence": 0.0,
                "error": str(e),
            }

    async def _extract_with_vision(
        self, image_base64: str, mime_type: str
    ) -> Dict[str, Any]:
        """Send the image to Grok and parse the JSON output."""

        # Build the category guide
        category_lines = []
        for i, c in enumerate(self.categories, 1):
            category_lines.append(f"{i}. {c['name']} — {c['description']}")
        category_list = "\n".join(category_lines)

        category_names = ", ".join(f'"{c["name"]}"' for c in self.categories)

        system_prompt = f"""You are a financial document extraction assistant.
Your task is to extract structured data from financial documents
(receipts, bills, invoices, statements, cheques, salary slips).

CRITICAL RULES:

1. READ THE IMAGE — do NOT hallucinate. If a value isn't on the document,
   return null.

2. RAW TEXT — return the full text you see on the document as a single
   string, preserving line breaks. Transcribe labels and values.

3. PAYEE NAME — the person or ORGANIZATION the payment is FOR.
   Priority:
     a) The company the bill/invoice is issued BY
        (e.g. "CLP Power", "AIA International Ltd", "HSBC")
     b) The merchant name on a receipt
     c) The employee (for reimbursements, MPF, or salary)
   Return the name EXACTLY as printed. If none is visible, return null.

4. TRANSACTION DATE — the date the transaction ACTUALLY occurred.
   Format: "YYYY-MM-DD". If a range is shown, use the start date.

5. TOTAL AMOUNT — look for a line that says one of:
   "Total", "Total Amount", "Total Amount Due", "Grand Total",
   "Amount Due", "Amount Payable", "Balance Due", "Net Amount",
   "Amount to Pay", "Pay This Amount"
   Chinese: 總額, 总额, 合計, 合计, 應付, 应付, 金額, 金额
   Extract that line's amount as "total_amount" (a number in HKD).
   If no total line exists, set "total_amount" to null.

6. LINE ITEMS — extract EVERY financial line from the document,
   INCLUDING the total line. Mark each item with:
   - "is_total": true only if that line is the total/amount-due row
   - "is_total": false otherwise

7. AMOUNT — for each line item, use the amount printed (in HKD;
   convert if needed).

8. DESCRIPTION — clear English description under 200 chars.

9. CATEGORY — pick EXACTLY ONE from this list (for reimbursements only):

{category_list}

   If nothing clearly fits, use null.

10. LANGUAGE — documents may be English, Chinese, or mixed.

11. DOCUMENT TYPE — one of: bill, receipt, mpf, cheque, invoice,
    salary, insurance, other.

OUTPUT FORMAT:
Return ONLY a valid JSON object. Do NOT wrap the JSON in markdown code
fences (no ```json blocks). Do NOT include any text before or after the
JSON. The response must start with {{ and end with }}.

The JSON must match this schema exactly:
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

        user_prompt = """Read this document and return the JSON described above.
Use the transaction date printed on the document (not today's date). Return
the JSON object only — no markdown, no explanations."""

        try:
            response = self.client.chat.completions.create(
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
            )

            content = response.choices[0].message.content
            print(f"📥 Grok raw response (first 200 chars): {content[:200]}")

            # Grok sometimes wraps JSON in ```json fences — strip them
            content = self._strip_json_fences(content)

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
            print(f"   Raw content that failed to parse: {content[:500]}")
            return {
                "raw_text": "", "payee_name": None, "document_type": "other",
                "total_amount": None, "items": [], "confidence": 0.0,
            }
        except Exception as e:
            print(f"❌ Grok vision extraction error: {e}")
            return {
                "raw_text": "", "payee_name": None, "document_type": "other",
                "total_amount": None, "items": [], "confidence": 0.0,
            }

    # ---------------- helpers ----------------

    def _strip_json_fences(self, content: str) -> str:
        """Remove ```json ... ``` fences if the model added them."""
        if not content:
            return content
        content = content.strip()

        # ```json ... ```
        if content.startswith("```"):
            # Remove opening fence
            first_newline = content.find("\n")
            if first_newline != -1:
                content = content[first_newline + 1:]
            else:
                content = content[3:]
            # Remove closing fence
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3]
            content = content.strip()

        # Handle a leading "json\n" without fences (some models)
        if content.lower().startswith("json\n"):
            content = content[5:].strip()

        return content

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

    def _get_mime_type(self, file_path: str) -> str:
        ext = file_path.lower().split(".")[-1]
        return {
            "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
            "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
            "tiff": "image/tiff", "tif": "image/tiff", "pdf": "application/pdf",
        }.get(ext, "image/jpeg")