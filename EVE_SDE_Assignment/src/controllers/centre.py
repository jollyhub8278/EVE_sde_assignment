from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.models.centre import Centre
from src.models.centre_offering import CentreTest
from src.models.diagnostic import DiagnosticTest
from src.schemas.centre import CentreResponse
from src.utils.db import get_db

router = APIRouter(prefix="/centres", tags=["Centres"])


@router.get("/", response_model=list[CentreResponse])
def get_centres(db: Session = Depends(get_db)):
    rows = (
        db.query(CentreTest, Centre, DiagnosticTest)
        .join(Centre, CentreTest.centre_id == Centre.id)
        .join(DiagnosticTest, CentreTest.test_id == DiagnosticTest.id)
        .all()
    )

    centres = {}

    for centre_test, centre, diagnostic_test in rows:
        if centre.id not in centres:
            centres[centre.id] = {
                "id": centre.id,
                "name": centre.name,
                "location": centre.location,
                "tests": [],
            }

        centres[centre.id]["tests"].append(
            {
                "id": diagnostic_test.id,
                "name": diagnostic_test.name,
                "price": float(centre_test.price),
            }
        )

    return list(centres.values())