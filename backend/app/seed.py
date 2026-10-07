"""
Seed companies, payment types, categories, and payees.
Source of truth: the Monthly / Annual Payment spreadsheet + the AD HOC additions.
Run with: python -m app.seed
Idempotent — safe to run multiple times.
"""
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import (
    Base, Company, PaymentType, PaymentCategory, Payee,
)


# ---- Companies ----
COMPANIES = [
    ("Leapstack International Limited", "LSI"),
    ("Leapstack Hong Kong Limited", "LSHK"),
    ("Leapstack Holding Limited", "LSH"),
]

# ---- Payment types ----
PAYMENT_TYPES = ["Monthly Payment", "Annual Payment", "AD HOC"]


# ---- Full category tree ----
# Structure: company_short → payment_type → [(category_name, frequency), ...]
TREE = {
    "LSI": {
        "Monthly Payment": [
            ("Salary", "monthly"),
            ("MPF", "monthly"),
            ("Reimbursement", "monthly"),
            ("Management Fee", "monthly"),
            ("Electricity Fee", "monthly"),
            ("Office Cleaning Service", "monthly"),
            ("Credit Card", "monthly"),
        ],
        "Annual Payment": [
            ("BR Renewal Fee", "annual"),
            ("Auditor Services", "annual"),
            ("Legal Consultation Fee", "annual"),
            ("Group Medical", "annual"),
            ("Employment Compensation", "annual"),
            ("Company Secretary Fee", "annual"),
        ],
        "AD HOC": [
            ("AD HOC Payment", "adhoc"),      # ← generic free-form AD HOC
            ("Petty Cash", "adhoc"),
            ("Room Booking Fee", "adhoc"),
            ("Legal Fee", "adhoc"),
        ],
    },
    "LSHK": {
        "Monthly Payment": [
            ("Salary", "monthly"),
            ("MPF", "monthly"),
            ("Reimbursement", "monthly"),
            ("Credit Card", "monthly"),
        ],
        "Annual Payment": [
            ("BR Renewal Fee", "annual"),
            ("Auditor Services", "annual"),
            ("Employment Compensation", "annual"),
            ("Company Secretary Fee", "annual"),
            ("Microsoft 365 Business Basic Pack", "annual"),
        ],
        "AD HOC": [
            ("AD HOC Payment", "adhoc"),      # ← generic free-form AD HOC
            ("Petty Cash", "adhoc"),
            ("Room Booking Fee", "adhoc"),
        ],
    },
    "LSH": {
        "Monthly Payment": [],
        "Annual Payment": [
            ("BR Renewal Fee", "annual"),
            ("Auditor Services", "annual"),
            ("Company Secretary Fee", "annual"),
        ],
        "AD HOC": [
            ("AD HOC Payment", "adhoc"),      # ← generic free-form AD HOC
            ("Petty Cash", "adhoc"),
        ],
    },
}


# ---- Default payees ----
# (name, type)
# The user can add more from the Review page's "+ Add payee" button.
PAYEES = [
    # ---- LSI Staff ----
    ("Chow Kwok Lim Stanley", "staff"),
    ("Gu Bai Chuan Cole", "staff"),
    ("Liu Gejie Jason", "staff"),
    ("Sun Motao", "staff"),
    ("Zhong Sirian", "staff"),
    ("Ren Yuan", "staff"),

    # ---- LSHK Staff ----
    ("Wong Hoi Nam Juliana", "staff"),
    ("Louise Danielle Sugiarto", "staff"),

    # ---- LSI Vendors ----
    ("Hong Kong Science and Technology Parks Corporation", "vendor"),
    ("CLP Power Hong Kong Limited", "vendor"),
    ("Johnson Cleaning Services Company Limited", "vendor"),
    ("The Hong Kong and Shanghai Banking Corporation", "vendor"),

    # ---- Annual Vendors ----
    ("The Government of the HKSAR", "vendor"),
    ("Eric H.T. Fan CPA (Practising)", "vendor"),
    ("S.K. Wong & Co", "vendor"),
    ("AIA International LTD", "vendor"),
    ("MSIG Insurance (Hong Kong) Ltd", "vendor"),
    ("Acota Limited", "vendor"),
    ("ACCESSORANGE LIMITED", "vendor"),

    # ---- AD HOC / third-party ----
    ("MICAN CAPITAL LIMITED", "vendor"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # ---------- Companies ----------
        company_by_short = {}
        for name, short in COMPANIES:
            c = db.query(Company).filter(Company.name == name).first()
            if not c:
                c = Company(name=name, short_name=short)
                db.add(c)
                db.flush()
                print(f"➕ Company: {name} ({short})")
            else:
                c.short_name = short
            company_by_short[short] = c

        # ---------- Payment types ----------
        type_map = {}
        for name in PAYMENT_TYPES:
            pt = db.query(PaymentType).filter(PaymentType.name == name).first()
            if not pt:
                pt = PaymentType(name=name)
                db.add(pt)
                db.flush()
                print(f"➕ Payment type: {name}")
            type_map[name] = pt

        # ---------- Categories ----------
        for short, tree in TREE.items():
            company = company_by_short[short]
            for type_name, cats in tree.items():
                pt = type_map[type_name]
                for cat_name, freq in cats:
                    exists = (
                        db.query(PaymentCategory)
                        .filter(
                            PaymentCategory.company_id == company.id,
                            PaymentCategory.payment_type_id == pt.id,
                            PaymentCategory.name == cat_name,
                        )
                        .first()
                    )
                    if not exists:
                        db.add(PaymentCategory(
                            company_id=company.id,
                            payment_type_id=pt.id,
                            name=cat_name,
                            frequency=freq,
                        ))
                        print(f"   ➕ {short} → {type_name} → {cat_name}")

        # ---------- Payees ----------
        for name, ptype in PAYEES:
            exists = db.query(Payee).filter(Payee.name == name).first()
            if not exists:
                db.add(Payee(name=name, payee_type=ptype))
                print(f"➕ Payee: {name} ({ptype})")

        db.commit()
        print("\n✅ Seed complete.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()