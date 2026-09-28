from src.models.centre import Centre
from src.models.centre_offering import CentreTest
from src.models.diagnostic import DiagnosticTest
from src.utils.db import SessionLocal


def seed_data():
    db = SessionLocal()

    try:
        existing_centre = db.query(Centre).first()

        if existing_centre:
            print("Sample data already exists.")
            return

        eve_diagnostics = Centre(
            name="EVE Diagnostics",
            location="Jaipur, Rajasthan",
        )

        health_first = Centre(
            name="HealthFirst Diagnostics",
            location="Sikar, Rajasthan",
        )

        db.add_all([eve_diagnostics, health_first])
        db.flush()

        cbc = DiagnosticTest(name="Complete Blood Count (CBC)")
        thyroid = DiagnosticTest(name="Thyroid Profile")
        hba1c = DiagnosticTest(name="HbA1c")

        db.add_all([cbc, thyroid, hba1c])
        db.flush()

        db.add_all([
            CentreTest(
                centre_id=eve_diagnostics.id,
                test_id=cbc.id,
                price=400.00,
            ),
            CentreTest(
                centre_id=eve_diagnostics.id,
                test_id=thyroid.id,
                price=650.00,
            ),
            CentreTest(
                centre_id=eve_diagnostics.id,
                test_id=hba1c.id,
                price=500.00,
            ),
            CentreTest(
                centre_id=health_first.id,
                test_id=cbc.id,
                price=350.00,
            ),
            CentreTest(
                centre_id=health_first.id,
                test_id=thyroid.id,
                price=600.00,
            ),
            CentreTest(
                centre_id=health_first.id,
                test_id=hba1c.id,
                price=450.00,
            ),
        ])

        db.commit()
        print("Sample data added successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()