from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.models.centre import Centre
from src.models.centre_offering import CentreTest
from src.models.diagnostic import DiagnosticTest
from src.models.user import User
from src.schemas.centre import CentreCreate, CentreResponse
from src.utils.db import get_db
from src.utils.dependencies import get_current_user

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

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_centre(
    centre_data: CentreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    centre_name = centre_data.name.strip()
    location = centre_data.location.strip()

    existing_centre = (
        db.query(Centre)
        .filter(
            Centre.name == centre_name,
            Centre.location == location,
        )
        .first()
    )

    if existing_centre:
        raise HTTPException(
            status_code=409,
            detail="Centre already exists",
        )

    centre = Centre(
        name=centre_name,
        location=location,
    )

    db.add(centre)
    db.flush()

    created_tests = []

    for test_data in centre_data.tests:
        test_name = test_data.name.strip()

        diagnostic_test = (
            db.query(DiagnosticTest)
            .filter(DiagnosticTest.name == test_name)
            .first()
        )

        if not diagnostic_test:
            diagnostic_test = DiagnosticTest(name=test_name)
            db.add(diagnostic_test)
            db.flush()

        centre_test = CentreTest(
            centre_id=centre.id,
            test_id=diagnostic_test.id,
            price=test_data.price,
        )

        db.add(centre_test)

        created_tests.append(
            {
                "id": diagnostic_test.id,
                "name": diagnostic_test.name,
                "price": float(test_data.price),
            }
        )

    db.commit()

    return {
        "id": centre.id,
        "name": centre.name,
        "location": centre.location,
        "tests": created_tests,
    }