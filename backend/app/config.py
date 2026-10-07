import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = os.getenv("APP_NAME", "Reimbursement IDP System")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./reimbursement.db")

    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "./outputs")
    USE_GCS: bool = os.getenv("USE_GCS", "False").lower() == "true"

    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    XAI_VISION_MODEL: str = os.getenv("XAI_VISION_MODEL", "grok-4.7")

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # ==================================================================
    # COMPANY TREE — from the spreadsheet
    # Company → Payment Type → Nature → [Payees]
    # ==================================================================
    COMPANY_TREE: dict = {
        "LSI": {
            "Monthly Payment": {
                "Salary": [
                    "Chow Kwok Lim Stanley",
                    "Gu Bai Chuan Cole",
                    "Liu Gejie Jason",
                    "Sun Motao",
                    "Zhong Sirian",
                    "Ren Yuan",
                ],
                "MPF": [
                    "Chow Kwok Lim Stanley",
                    "Gu Bai Chuan Cole",
                    "Liu Gejie Jason",
                    "Sun Motao",
                ],
                "Reimbursement": [
                    "Chow Kwok Lim Stanley",
                    "Gu Bai Chuan Cole",
                ],
                "Management Fee": [
                    "Hong Kong Science and Technology Parks Corporation",
                ],
                "Electricity Fee": [
                    "CLP Power Hong Kong Limited",
                ],
                "Office Cleaning Service": [
                    "Johnson Cleaning Services Company Limited",
                ],
            },
            "Annual Payment": {
                "BR Renewal Fee": ["The Government of the HKSAR"],
                "Auditor Services": ["Eric H.T. Fan CPA (Practising)"],
                "Legal Consultation Fee": ["S.K. Wong & Co"],
                "Group Medical": ["AIA International LTD"],
                "Employment Compensation": ["MSIG Insurance (Hong Kong) Ltd"],
                "Company Secretary Fee": ["Acota Limited"],
            },
            "AD HOC": {
                "AD HOC Payment": [],
                "Petty Cash": [],
                "Room Booking Fee": [],
                "Legal Fee": [],
            },
        },
        "LSHK": {
            "Monthly Payment": {
                "Salary": [
                    "Wong Hoi Nam Juliana",
                    "Louise Danielle Sugiarto",
                ],
                "MPF": ["Wong Hoi Nam Juliana"],
                "Reimbursement": ["Wong Hoi Nam Juliana"],
                "Credit Card": ["The Hong Kong and Shanghai Banking Corporation"],
            },
            "Annual Payment": {
                "BR Renewal Fee": ["The Government of the HKSAR"],
                "Auditor Services": ["Eric H.T. Fan CPA (Practising)"],
                "Employment Compensation": ["MSIG Insurance (Hong Kong) Ltd"],
                "Company Secretary Fee": ["Acota Limited"],
                "Microsoft 365 Business Basic Pack": ["ACCESSORANGE LIMITED"],
            },
            "AD HOC": {
                "AD HOC Payment": [],
                "Petty Cash": [],
                "Room Booking Fee": [],
            },
        },
        "LSH": {
            "Monthly Payment": {},
            "Annual Payment": {
                "BR Renewal Fee": ["The Government of the HKSAR"],
                "Auditor Services": ["Eric H.T. Fan CPA (Practising)"],
                "Company Secretary Fee": ["Acota Limited"],
            },
            "AD HOC": {
                "AD HOC Payment": [],
                "Petty Cash": [],
            },
        },
    }

    # ==================================================================
    # ALIASES — what the AI might return for a payee name
    # ==================================================================
    PAYEE_ALIASES: dict = {
        # LSI staff
        "chow kwok lim stanley": "Chow Kwok Lim Stanley",
        "stanley chow": "Chow Kwok Lim Stanley",
        "chow kwok lim": "Chow Kwok Lim Stanley",
        "kwok lim": "Chow Kwok Lim Stanley",
        "stanley": "Chow Kwok Lim Stanley",
        "周國廉": "Chow Kwok Lim Stanley",
        "周国廉": "Chow Kwok Lim Stanley",

        "gu bai chuan cole": "Gu Bai Chuan Cole",
        "cole gu": "Gu Bai Chuan Cole",
        "gu bai chuan": "Gu Bai Chuan Cole",
        "bai chuan gu": "Gu Bai Chuan Cole",
        "bai chuan": "Gu Bai Chuan Cole",
        "cole": "Gu Bai Chuan Cole",
        "古百川": "Gu Bai Chuan Cole",
        "顾百川": "Gu Bai Chuan Cole",

        "liu gejie jason": "Liu Gejie Jason",
        "jason liu": "Liu Gejie Jason",
        "gejie liu": "Liu Gejie Jason",
        "jason": "Liu Gejie Jason",
        "劉格杰": "Liu Gejie Jason",
        "刘格杰": "Liu Gejie Jason",

        "sun motao": "Sun Motao",
        "motao sun": "Sun Motao",
        "孫墨濤": "Sun Motao",
        "孙墨涛": "Sun Motao",

        "zhong sirian": "Zhong Sirian",
        "sirian zhong": "Zhong Sirian",

        "ren yuan": "Ren Yuan",
        "yuan ren": "Ren Yuan",

        # LSHK staff
        "wong hoi nam juliana": "Wong Hoi Nam Juliana",
        "juliana wong": "Wong Hoi Nam Juliana",
        "hoi nam wong": "Wong Hoi Nam Juliana",
        "juliana": "Wong Hoi Nam Juliana",
        "黃海嵐": "Wong Hoi Nam Juliana",
        "黄海岚": "Wong Hoi Nam Juliana",

        "louise danielle sugiarto": "Louise Danielle Sugiarto",
        "louise sugiarto": "Louise Danielle Sugiarto",
        "louise": "Louise Danielle Sugiarto",

        # LSI vendors
        "hong kong science and technology parks corporation":
            "Hong Kong Science and Technology Parks Corporation",
        "hkstp": "Hong Kong Science and Technology Parks Corporation",
        "hk science park": "Hong Kong Science and Technology Parks Corporation",
        "science park": "Hong Kong Science and Technology Parks Corporation",
        "hksciencepark": "Hong Kong Science and Technology Parks Corporation",

        "clp power hong kong limited": "CLP Power Hong Kong Limited",
        "clp power": "CLP Power Hong Kong Limited",
        "clp": "CLP Power Hong Kong Limited",

        "johnson cleaning services company limited":
            "Johnson Cleaning Services Company Limited",
        "johnson cleaning services": "Johnson Cleaning Services Company Limited",
        "johnson cleaning": "Johnson Cleaning Services Company Limited",

        "the hong kong and shanghai banking corporation":
            "The Hong Kong and Shanghai Banking Corporation",
        "hongkong bank": "The Hong Kong and Shanghai Banking Corporation",
        "hong kong and shanghai banking":
            "The Hong Kong and Shanghai Banking Corporation",
        "hsbc": "The Hong Kong and Shanghai Banking Corporation",

        # Annual vendors
        "the government of the hksar": "The Government of the HKSAR",
        "government of hksar": "The Government of the HKSAR",
        "hksar": "The Government of the HKSAR",
        "gov hksar": "The Government of the HKSAR",

        "eric h.t. fan cpa (practising)": "Eric H.T. Fan CPA (Practising)",
        "eric h.t. fan cpa": "Eric H.T. Fan CPA (Practising)",
        "eric ht fan cpa": "Eric H.T. Fan CPA (Practising)",
        "eric fan": "Eric H.T. Fan CPA (Practising)",
        "fan cpa": "Eric H.T. Fan CPA (Practising)",

        "s.k. wong & co": "S.K. Wong & Co",
        "sk wong & co": "S.K. Wong & Co",
        "sk wong": "S.K. Wong & Co",
        "s.k. wong": "S.K. Wong & Co",

        "aia international ltd": "AIA International LTD",
        "aia international": "AIA International LTD",
        "aia": "AIA International LTD",

        "msig insurance (hong kong) ltd": "MSIG Insurance (Hong Kong) Ltd",
        "msig insurance": "MSIG Insurance (Hong Kong) Ltd",
        "msig": "MSIG Insurance (Hong Kong) Ltd",

        "acota limited": "Acota Limited",
        "acota": "Acota Limited",

        "accessorange limited": "ACCESSORANGE LIMITED",
        "accessorange": "ACCESSORANGE LIMITED",

        # AD HOC
        "mican capital limited": "MICAN CAPITAL LIMITED",
        "mican capital": "MICAN CAPITAL LIMITED",
        "mican": "MICAN CAPITAL LIMITED",
        "mcl": "MICAN CAPITAL LIMITED",
    }

    # ==================================================================
    # NATURE KEYWORDS — text patterns that identify a nature
    # ==================================================================
    NATURE_KEYWORDS: dict = {
        "Group Medical": [
            "group medical", "medical insurance", "health insurance",
            "insurance premium", "policy no", "policy number",
            "annual insurance", "medical plan", "aia",
            "團體醫療", "团体医疗", "保險", "保险",
        ],
        "MPF": [
            "mpf", "mandatory provident fund", "mpf contribution",
            "mpf statement", "retirement fund", "stronger mpf",
            "強積金", "强积金",
        ],
        "Employment Compensation": [
            "employment compensation", "employee compensation",
            "employees compensation", "workmen compensation",
            "workers compensation", "msig",
            "僱員補償", "雇员补偿",
        ],
        "BR Renewal Fee": [
            "br renewal", "business registration", "business registration fee",
            "br fee", "business registration office",
            "商業登記", "商业登记",
        ],
        "Auditor Services": [
            "auditor", "audit fee", "audit report", "audit service",
            "cpa", "eric fan",
            "核數", "核数",
        ],
        "Company Secretary Fee": [
            "company secretary", "corporate secretary", "secretarial fee",
            "公司秘書", "公司秘书",
        ],
        "Legal Consultation Fee": [
            "legal consultation", "legal fee", "solicitor", "lawyer",
            "法律諮詢", "法律咨询",
        ],
        "Software Annual Fee": [
            "software annual", "annual software", "wps",
            "軟件年費", "软件年费",
        ],
        "Microsoft 365 Business Basic Pack": [
            "microsoft 365", "m365", "office 365", "business basic",
        ],
        "Management Fee": [
            "management fee", "management service", "hkstp",
            "science park", "management charges",
            "管理費", "管理费",
        ],
        "Electricity Fee": [
            "electricity", "electricity bill", "power bill", "utility bill",
            "clp", "clp power", "electric bill", "electricity charges",
            "電費", "电费",
        ],
        "Office Cleaning Service": [
            "office cleaning", "cleaning service", "cleaning services",
            "johnson cleaning",
            "清潔服務", "清洁服务",
        ],
        "Credit Card": [
            "credit card", "visa card", "mastercard", "credit card statement",
            "信用卡",
        ],
        "Salary": [
            "salary", "payroll", "monthly salary", "salary slip",
            "payslip", "staff salary",
            "薪金", "薪水", "工資", "工资",
        ],
        "Reimbursement": [
            "reimbursement", "expense claim", "staff reimbursement",
            "expense report", "expense reimbursement",
            "報銷", "报销", "費用報銷",
        ],
    }

    # Order used when a payee has no nature yet (prefer reimbursement-style)
    NATURE_PREFERRED_ORDER: list = [
        "Reimbursement", "Salary", "MPF", "Group Medical",
        "Management Fee", "Electricity Fee", "Office Cleaning Service",
        "Credit Card", "BR Renewal Fee", "Auditor Services",
        "Legal Consultation Fee", "Employment Compensation",
        "Company Secretary Fee", "Microsoft 365 Business Basic Pack",
        "Software Annual Fee", "AD HOC Payment", "Petty Cash",
        "Room Booking Fee", "Legal Fee",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)