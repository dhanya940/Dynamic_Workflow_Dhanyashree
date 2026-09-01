"""Pydantic schemas for Tasks 4-6 and the supporting submission/rule flow."""
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field as PydanticField, ConfigDict

class FieldOptionCreate(BaseModel):
    option_label: str
    option_value: str
    display_order: int = 0

class FieldOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    option_label: str
    option_value: str
    display_order: int

class FieldCreate(BaseModel):
    label: str
    field_type: str
    placeholder: str | None = None
    is_required: bool = False
    validation_config: dict[str, Any] | None = None
    options: list[FieldOptionCreate] | None = None

class FieldUpdate(BaseModel):
    label: str | None = None
    field_type: str | None = None
    placeholder: str | None = None
    is_required: bool | None = None
    validation_config: dict[str, Any] | None = None
    options: list[FieldOptionCreate] | None = None

class FieldOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    label: str
    field_type: str
    placeholder: str | None
    is_required: bool
    display_order: int
    validation_config: dict[str, Any] | None
    options: list[FieldOptionOut] = []

class ReorderItem(BaseModel):
    field_id: uuid.UUID
    display_order: int

class ReorderFieldsRequest(BaseModel):
    order: list[ReorderItem]

class FormCreate(BaseModel):
    title: str
    description: str | None = None

class FormUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class FormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

class FormDetailOut(FormOut):
    fields: list[FieldOut] = []
    editing_version_number: int

class FormListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    status: str
    updated_at: datetime

class ConditionalRuleCreate(BaseModel):
    trigger_field_id: uuid.UUID
    operator: str
    comparison_value: str
    target_field_id: uuid.UUID
    action: str = "show"

class ConditionalRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    trigger_field_id: uuid.UUID
    operator: str
    comparison_value: str
    target_field_id: uuid.UUID
    action: str

class FormVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    version_number: int
    is_active: bool
    published_at: datetime | None

class FormVersionDetailOut(FormVersionOut):
    fields: list[FieldOut] = []
    rules: list[ConditionalRuleOut] = []

class ShareLinkOut(BaseModel):
    slug: str
    public_url: str
    form_version_number: int

class PublicFormOut(BaseModel):
    title: str
    description: str | None
    fields: list[FieldOut]
    rules: list[ConditionalRuleOut] = []

class SubmissionCreate(BaseModel):
    values: dict[str, Any]
    completion_time_seconds: int | None = PydanticField(default=None, ge=0)

class SubmissionOut(BaseModel):
    response_id: uuid.UUID
    submitted_at: datetime
    message: str
