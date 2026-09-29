import os
from decimal import Decimal

os.environ["TESTING"] = "1"

import pytest

import src.models
from src.models.centre import Centre
from src.models.centre_offering import CentreTest
from src.models.diagnostic import DiagnosticTest
from src.utils.db import Base, SessionLocal, engine


@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        centre_one = Centre(
            name="Test Diagnostics Centre",
            location="Test City",
        )

        centre_two = Centre(
            name="Second Test Diagnostics Centre",
            location="Second Test City",
        )

        cbc_test = DiagnosticTest(
            name="Complete Blood Count (CBC)",
        )

        thyroid_test = DiagnosticTest(
            name="Thyroid Profile",
        )

        db.add_all([
            centre_one,
            centre_two,
            cbc_test,
            thyroid_test,
        ])
        db.flush()

        db.add_all([
            CentreTest(
                centre_id=centre_one.id,
                test_id=cbc_test.id,
                price=Decimal("400.00"),
            ),
            CentreTest(
                centre_id=centre_two.id,
                test_id=thyroid_test.id,
                price=Decimal("600.00"),
            ),
        ])

        db.commit()

        yield
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)