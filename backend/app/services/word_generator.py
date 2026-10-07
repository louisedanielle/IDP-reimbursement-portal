from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from docx import Document as DocxDocument
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

from ..config import settings


DEFAULT_COMPANY_NAME = "Leapstack International Limited"
DEFAULT_COMPANY_ADDRESS = (
    "Unit 105A, 1/F., Building 5W, 5 Science Park West Avenue, "
    "Hong Kong Science Park, Shatin."
)
DEFAULT_COMPANY_CONTACT = "Tel:+852 3628 5039  Fax +852 3105 5299"

PAYMENT_DETAILS_BASE_URL = "http://localhost:8000"


class WordGenerator:
    """
    Generates a Payment Requisition Word document.
    Works for ANY nature (Salary, MPF, Reimbursement, AD HOC, etc.).

    Behavior:
      - Reimbursement: groups line items by expense category, one row per
        category with subtotal.
      - Non-reimbursement (AD HOC, Salary, MPF, ...): one row per line item.
        The Date column shows a value only on the FIRST row; subsequent rows
        leave it blank. Multi-line particulars are preserved.
    """

    def __init__(self):
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)

    # ------------------------------------------------------------------
    # PUBLIC
    # ------------------------------------------------------------------

    def generate_requisition_docx(self, data: Dict[str, Any]) -> str:
        doc = DocxDocument()

        for section in doc.sections:
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2)
            section.right_margin = Cm(2)

        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(10)
        style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)

        # --- Company header ---
        self._add_company_header(
            doc,
            data.get("company_name") or DEFAULT_COMPANY_NAME,
            data.get("company_address") or DEFAULT_COMPANY_ADDRESS,
            data.get("company_contact") or DEFAULT_COMPANY_CONTACT,
        )

        # --- Title ---
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = title.add_run("PAYMENT REQUISITION")
        r.bold = True
        r.font.size = Pt(14)
        title.paragraph_format.space_after = Pt(12)

        # --- Detect mode ---
        nature_name = (data.get("category_name") or "").strip().lower()
        is_reimbursement = nature_name == "reimbursement"

        # --- Compute totals ---
        line_items = data.get("line_items", [])
        if is_reimbursement:
            grouped = self._group_by_category(line_items)
            grand_total = sum(
                sum(i["amount_hkd"] for i in g) for g in grouped.values()
            )
        else:
            grouped = {}
            grand_total = sum(i.get("amount_hkd", 0) for i in line_items)

        # --- Info block ---
        info_rows = [
            ("PR No.:", data["pr_number"]),
            ("Applicant:", data.get("applicant", "Juliana")),
            ("Nature:", data.get("category_name") or data.get("nature", "Payment Requisition")),
            ("", ""),
            ("Name of Payee:", data.get("payee_name", "")),
            ("Amount payable:", f"HK${grand_total:,.2f}"),
        ]
        if data.get("period"):
            info_rows.insert(3, ("Period:", data["period"]))

        for label, value in info_rows:
            self._add_field(doc, label, value)

        doc.add_paragraph()

        # --- Table: Date | Particular | Expenses HK$ | Exch Rate | US$ ---
        headers = ["Date", "Particular", "Expenses in\nHK$", "Exch\nRate", "US$"]
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        hdr = table.rows[0].cells
        for i, text in enumerate(headers):
            hdr[i].text = ""
            p = hdr[i].paragraphs[0]
            r = p.add_run(text)
            r.bold = True
            r.font.size = Pt(9)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        display_date = self._earliest_date(line_items)

        if is_reimbursement:
            # ---------- REIMBURSEMENT: one row per category ----------
            for category, group in grouped.items():
                row = table.add_row().cells
                subtotal = sum(i["amount_hkd"] for i in group)

                row[0].text = display_date
                row[1].text = category
                row[2].text = f"{subtotal:,.2f}"
                row[3].text = ""
                row[4].text = ""

                row[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                row[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                row[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                row[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            # ---------- NON-REIMBURSEMENT: one row per line item ----------
            # The Date column is only filled on the FIRST row.
            for idx, item in enumerate(line_items):
                row = table.add_row().cells

                # Date only on the first row
                if idx == 0:
                    date_str = item.get("date", "")
                    if isinstance(date_str, datetime):
                        date_str = date_str.strftime("%Y-%m-%d")
                    elif "T" in str(date_str):
                        date_str = str(date_str).split("T")[0]
                    row[0].text = str(date_str)
                else:
                    row[0].text = ""

                # Amount
                row[2].text = f"{item.get('amount_hkd', 0):,.2f}"
                row[3].text = ""
                row[4].text = ""

                row[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
                row[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
                row[3].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                row[4].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

                # Particular cell — preserve line breaks
                row[1].text = ""
                cell_para = row[1].paragraphs[0]
                desc = (item.get("description") or "").replace("\r\n", "\n")
                lines = desc.split("\n")
                for i, line in enumerate(lines):
                    if i > 0:
                        cell_para.add_run().add_break()
                    cell_para.add_run(line)
                row[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT

        # --- Blank spacer rows (matches reference layout) ---
        for _ in range(2):
            table.add_row()

        # --- Total row ---
        total_row = table.add_row().cells
        total_row[0].merge(total_row[1])
        p = total_row[0].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        p = total_row[2].paragraphs[0]
        r = p.add_run(f"{grand_total:,.2f}")
        r.bold = True
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # --- "Click here for payment details" — only for reimbursements ---
        if is_reimbursement:
            doc.add_paragraph()
            link_p = doc.add_paragraph()
            details_url = (
                f"{PAYMENT_DETAILS_BASE_URL}/api/requisitions/"
                f"{data.get('requisition_id', '')}/export/excel"
            )
            self._add_hyperlink(link_p, "Click here for payment details", details_url)

        # --- Cheque No. ---
        doc.add_paragraph()
        cheque_p = doc.add_paragraph()
        cheque_p.add_run("Cheque No.").font.size = Pt(10)

        # --- Signature block ---
        doc.add_paragraph()
        doc.add_paragraph()

        sig_name = doc.add_paragraph()
        r = sig_name.add_run(data.get("applicant", "Juliana"))
        r.italic = True
        r.font.size = Pt(16)

        underline = doc.add_paragraph()
        underline.add_run("_" * 30).font.size = Pt(10)

        label = doc.add_paragraph()
        label.add_run(data.get("applicant", "Juliana")).font.size = Pt(9)

        doc.add_paragraph()
        approved_p = doc.add_paragraph()
        approved_p.add_run("Approved by:").font.size = Pt(10)

        doc.add_paragraph()
        doc.add_paragraph()
        underline2 = doc.add_paragraph()
        underline2.add_run("_" * 30).font.size = Pt(10)

        # --- Save ---
        filename = (
            f"PR_{data['pr_number']}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        )
        filepath = self.output_dir / filename
        doc.save(filepath)

        return str(filepath)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _add_company_header(self, doc, name: str, address: str, contact: str) -> None:
        for text, bold, size in [
            (name, True, 11),
            (address, False, 9),
            (contact, False, 9),
        ]:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(text)
            r.bold = bold
            r.font.size = Pt(size)
            p.paragraph_format.space_after = Pt(0)

    def _add_field(self, doc, label: str, value: str) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        if label:
            r = p.add_run(f"{label}    ")
            r.bold = True
            r.font.size = Pt(10)
        else:
            r = p.add_run(" " * 8)
            r.font.size = Pt(10)
        r2 = p.add_run(str(value))
        r2.font.size = Pt(10)

    def _add_hyperlink(self, paragraph, text: str, url: str) -> None:
        """Insert a clickable hyperlink into a python-docx paragraph."""
        from docx.oxml.shared import OxmlElement, qn

        part = paragraph.part
        r_id = part.relate_to(
            url,
            "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
            is_external=True,
        )

        hyperlink = OxmlElement("w:hyperlink")
        hyperlink.set(qn("r:id"), r_id)

        new_run = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")

        color = OxmlElement("w:color")
        color.set(qn("w:val"), "0563C1")
        rPr.append(color)

        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

        new_run.append(rPr)

        t = OxmlElement("w:t")
        t.text = text
        new_run.append(t)

        hyperlink.append(new_run)
        paragraph._p.append(hyperlink)

    def _earliest_date(self, items: List[Dict[str, Any]]) -> str:
        """Return the earliest receipt date as YYYY-MM (or YYYY-MM-DD if
        the first item has a full date). Used for the reimbursement table."""
        dates = []
        for item in items:
            d = item.get("date")
            if not d:
                continue
            if isinstance(d, datetime):
                dates.append(d)
                continue
            s = str(d)
            for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    dates.append(datetime.strptime(s[:10], fmt))
                    break
                except ValueError:
                    continue
        if dates:
            return min(dates).strftime("%Y-%m")
        return datetime.now().strftime("%Y-%m")

    def _group_by_category(self, line_items):
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for item in line_items:
            category = (item.get("category") or "Miscellaneous").strip() or "Miscellaneous"
            groups.setdefault(category, []).append(item)
        return groups