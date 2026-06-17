import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.patient import PatientCreate, PatientUpdate, PatientOut
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.routers.auth import get_current_doctor

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientOut, status_code=201)
def create_patient(
    body: PatientCreate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    patient = Patient(doctor_id=doctor.id, **body.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientOut])
def list_patients(
    q: str | None = None,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    query = db.query(Patient).filter(Patient.doctor_id == doctor.id, Patient.is_deleted == False)
    if q:
        query = query.filter(Patient.name.ilike(f"%{q}%"))
    return query.order_by(Patient.name).all()


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: uuid.UUID,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    p = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.doctor_id == doctor.id,
        Patient.is_deleted == False,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


@router.put("/{patient_id}", response_model=PatientOut)
def update_patient(
    patient_id: uuid.UUID,
    body: PatientUpdate,
    doctor: Doctor = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    p = db.query(Patient).filter(
        Patient.id == patient_id,
        Patient.doctor_id == doctor.id,
        Patient.is_deleted == False,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p
