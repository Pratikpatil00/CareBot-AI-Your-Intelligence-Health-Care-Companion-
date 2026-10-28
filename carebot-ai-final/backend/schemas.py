from datetime import date
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1,max_length=6000)]
Short = Annotated[str, StringConstraints(strip_whitespace=True,min_length=1,max_length=120)]
Clock = Annotated[str, StringConstraints(pattern=r'^(?:[01]\d|2[0-3]):[0-5]\d$')]
class Input(BaseModel):
    model_config = ConfigDict(extra='forbid',allow_inf_nan=False)
class Auth(Input):
    name: Short
    password: Annotated[str,StringConstraints(min_length=8,max_length=128)]
    consent: Literal[True]
    height_cm: float | None = Field(None,ge=30,le=250)
    weight_kg: float | None = Field(None,gt=0,le=500)
class ProfileInput(Input):
    age: int | None = Field(None,ge=1,le=120)
    gender: str = Field('',max_length=30)
    weight_kg: float | None = Field(None,gt=0,le=500)
    height_cm: float | None = Field(None,ge=30,le=250)
    known_conditions: str = Field('',max_length=3000)
    preferences: str = Field('',max_length=1500)
    allergies: str = Field('',max_length=1500)
    water_target_ml: int = Field(2000,ge=250,le=6000)
    water_reminder_minutes: int = Field(0,ge=0,le=240)
    timezone: str = 'Asia/Kolkata'
    @field_validator('timezone')
    @classmethod
    def zone(cls,v):
        try: ZoneInfo(v)
        except (ZoneInfoNotFoundError,ValueError): raise ValueError('Unknown IANA timezone')
        return v
class MeasurementInput(Input):
    bp_systolic: int | None = Field(None,ge=40,le=300)
    bp_diastolic: int | None = Field(None,ge=20,le=200)
    heart_rate: int | None = Field(None,ge=20,le=250)
    weight_kg: float | None = Field(None,gt=0,le=500)
    height_cm: float | None = Field(None,ge=30,le=250)
    @model_validator(mode='after')
    def reading(self):
        if all(v is None for v in self.model_dump().values()): raise ValueError('Enter at least one reading')
        if self.bp_systolic and self.bp_diastolic and self.bp_diastolic >= self.bp_systolic: raise ValueError('Diastolic must be below systolic')
        return self
class MedicineInput(Input):
    name: Short
    dosage: Short
    instructions: str = Field('',max_length=1000)
    schedule_times: list[Clock] = Field(min_length=1,max_length=8)
    start_date: date
    end_date: date | None = None
    reminder_enabled: bool = True
    @model_validator(mode='after')
    def dates(self):
        if self.end_date and self.end_date < self.start_date: raise ValueError('End date must follow start date')
        self.schedule_times = sorted(set(self.schedule_times))
        return self
class DoseInput(Input):
    scheduled_date: date
    scheduled_time: Clock
    status: Literal['taken','missed']
class WaterInput(Input):
    amount_ml: int = Field(ge=1,le=3000)
class ChatInput(Input):
    message: Text
    thread_id: UUID
class SymptomInput(Input):
    symptoms: Text
class DietInput(Input):
    goal: Text = 'A balanced daily eating plan'
class LabField(BaseModel):
    field: str
    value: str | None = None
    unit: str | None = None
    reference_range: str | None = None
    status: Literal['as_reported_normal','as_reported_high','as_reported_low','unknown'] = 'unknown'
class ReportResult(BaseModel):
    fields: list[LabField]
    explanation: str
    follow_up: list[str]
    uncertainties: list[str]
class PrescriptionMedicine(BaseModel):
    name: str | None
    dosage: str | None
    frequency: str | None
    instructions: str | None
    duration: str | None
    source_text: str
    needs_review: bool = True
class PrescriptionResult(BaseModel):
    medicines: list[PrescriptionMedicine]
    uncertainties: list[str]
    explanation: str
class SymptomResult(BaseModel):
    possible_causes: list[str]
    urgency: Literal['emergency','urgent','routine','uncertain']
    explanation: str
    next_steps: list[str]
    specialty: str
class DietResult(BaseModel):
    overview: str
    meals: list[str]
    considerations: list[str]
class SpecialistResult(BaseModel):
    specialty: str
    explanation: str
    urgency: Literal['emergency','urgent','routine','uncertain']
class XrayResult(BaseModel):
    observations: list[str]
    explanation: str
    limitations: list[str]
    next_steps: list[str]
