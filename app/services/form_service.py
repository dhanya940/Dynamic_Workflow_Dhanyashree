"""Business logic for Tasks 4-6 plus the supporting dynamic-rule/submission flow."""
import secrets
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.form import Form
from app.models.form_version import FormVersion
from app.models.field import Field
from app.models.field_option import FieldOption
from app.models.conditional_rule import ConditionalRule
from app.models.submission import Submission
from app.models.response_value import ResponseValue
from app.models.form_share_link import FormShareLink
from app.schemas.form import (
    FormCreate, FormUpdate, FieldCreate, FieldUpdate, ReorderFieldsRequest,
    ConditionalRuleCreate, SubmissionCreate,
)

def get_form_or_404(db: Session, form_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Form:
    q = db.query(Form).filter(Form.id == form_id)
    if user_id is not None:
        q = q.filter(Form.created_by == user_id)
    form = q.first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form

def create_form(db: Session, form_in: FormCreate, user_id: uuid.UUID) -> Form:
    form = Form(title=form_in.title.strip(), description=form_in.description, created_by=user_id)
    db.add(form); db.commit(); db.refresh(form)
    return form

def _latest_version(db: Session, form: Form) -> FormVersion | None:
    return db.query(FormVersion).filter(FormVersion.form_id == form.id).order_by(FormVersion.version_number.desc()).first()

def get_form_with_fields(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> tuple[Form, FormVersion | None]:
    form = get_form_or_404(db, form_id, user_id)
    return form, _latest_version(db, form)

def update_form(db: Session, form_id: uuid.UUID, form_in: FormUpdate, user_id: uuid.UUID) -> Form:
    form = get_form_or_404(db, form_id, user_id)
    if form.status == "archived":
        raise HTTPException(status_code=400, detail="Archived forms cannot be edited")
    # Per Task 5, edits to a published form branch a new draft rather than mutating the live version.
    if form.status == "published":
        _get_or_create_draft_version(db, form)
        form.status = "draft"
    if form_in.title is not None:
        form.title = form_in.title
    if form_in.description is not None:
        form.description = form_in.description
    form.updated_at = datetime.utcnow()
    db.commit(); db.refresh(form)
    return form

def archive_form(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> Form:
    form = get_form_or_404(db, form_id, user_id)
    form.status = "archived"; form.updated_at = datetime.utcnow()
    db.commit(); db.refresh(form)
    return form

def _clone_fields_and_rules(db: Session, source: FormVersion, target: FormVersion) -> None:
    mapping = {}
    for field in sorted(source.fields, key=lambda f: f.display_order):
        nf = Field(form_version_id=target.id, label=field.label, field_type=field.field_type,
                   placeholder=field.placeholder, is_required=field.is_required,
                   display_order=field.display_order, validation_config=field.validation_config)
        db.add(nf); db.flush(); mapping[field.id] = nf.id
        for opt in sorted(field.options, key=lambda o: o.display_order):
            db.add(FieldOption(field_id=nf.id, option_label=opt.option_label,
                               option_value=opt.option_value, display_order=opt.display_order))
    db.flush()
    for rule in source_rules(source):
        if rule.trigger_field_id in mapping and rule.target_field_id in mapping:
            db.add(ConditionalRule(trigger_field_id=mapping[rule.trigger_field_id],
                                    target_field_id=mapping[rule.target_field_id],
                                    operator=rule.operator,
                                    comparison_value=rule.comparison_value, action=rule.action))

def source_rules(source: FormVersion):
    ids = {f.id for f in source.fields}
    rules = []
    # Relationships are not defined on FormVersion, so use the session in caller instead.
    return rules

def _clone_rules(db: Session, source: FormVersion, mapping: dict):
    old_rules = db.query(ConditionalRule).filter(
        ConditionalRule.trigger_field_id.in_(list(mapping.keys())),
        ConditionalRule.target_field_id.in_(list(mapping.keys()))
    ).all()
    for r in old_rules:
        db.add(ConditionalRule(trigger_field_id=mapping[r.trigger_field_id],
                               target_field_id=mapping[r.target_field_id],
                               operator=r.operator, comparison_value=r.comparison_value, action=r.action))

def _get_or_create_draft_version(db: Session, form: Form) -> FormVersion:
    latest = _latest_version(db, form)
    if latest is None:
        draft = FormVersion(form_id=form.id, version_number=1, is_active=False)
        db.add(draft); db.commit(); db.refresh(draft); return draft
    if not latest.is_active:
        return latest
    draft = FormVersion(form_id=form.id, version_number=latest.version_number + 1, is_active=False)
    db.add(draft); db.flush()
    mapping = {}
    for field in sorted(latest.fields, key=lambda f: f.display_order):
        nf = Field(form_version_id=draft.id, label=field.label, field_type=field.field_type,
                   placeholder=field.placeholder, is_required=field.is_required,
                   display_order=field.display_order, validation_config=field.validation_config)
        db.add(nf); db.flush(); mapping[field.id] = nf.id
        for opt in sorted(field.options, key=lambda o: o.display_order):
            db.add(FieldOption(field_id=nf.id, option_label=opt.option_label,
                               option_value=opt.option_value, display_order=opt.display_order))
    db.flush(); _clone_rules(db, latest, mapping)
    db.commit(); db.refresh(draft); return draft

def _branch_draft_with_mapping(db: Session, form: Form, source: FormVersion):
    draft = FormVersion(form_id=form.id, version_number=source.version_number + 1, is_active=False)
    db.add(draft); db.flush()
    mapping = {}
    for old in sorted(source.fields, key=lambda f: f.display_order):
        nf = Field(form_version_id=draft.id, label=old.label, field_type=old.field_type,
                   placeholder=old.placeholder, is_required=old.is_required,
                   display_order=old.display_order, validation_config=old.validation_config)
        db.add(nf); db.flush(); mapping[old.id] = nf.id
        for opt in sorted(old.options, key=lambda o: o.display_order):
            db.add(FieldOption(field_id=nf.id, option_label=opt.option_label,
                               option_value=opt.option_value, display_order=opt.display_order))
    db.flush(); _clone_rules(db, source, mapping)
    db.commit(); db.refresh(draft)
    return draft, mapping

def add_field(db: Session, form_id: uuid.UUID, field_in: FieldCreate, user_id: uuid.UUID) -> Field:
    form = get_form_or_404(db, form_id, user_id)
    if form.status == "archived": raise HTTPException(status_code=400, detail="Cannot modify an archived form")
    draft = _get_or_create_draft_version(db, form)
    field = Field(form_version_id=draft.id, label=field_in.label, field_type=field_in.field_type,
                  placeholder=field_in.placeholder, is_required=field_in.is_required,
                  display_order=max([f.display_order for f in draft.fields], default=-1)+1,
                  validation_config=field_in.validation_config)
    db.add(field); db.flush()
    for opt in field_in.options or []:
        db.add(FieldOption(field_id=field.id, option_label=opt.option_label,
                           option_value=opt.option_value, display_order=opt.display_order))
    form.status = "draft"; form.updated_at = datetime.utcnow()
    db.commit(); db.refresh(field); return field

def update_field(db: Session, field_id: uuid.UUID, field_in: FieldUpdate, user_id: uuid.UUID) -> Field:
    field = db.query(Field).join(FormVersion).join(Form).filter(
        Field.id == field_id, Form.created_by == user_id
    ).first()
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")
    form = field.form_version.form
    if form.status == "archived":
        raise HTTPException(status_code=400, detail="Archived forms cannot be edited")
    if field.form_version.is_active:
        old_id = field.id
        draft, mapping = _branch_draft_with_mapping(db, form, field.form_version)
        field = db.query(Field).filter(Field.id == mapping[old_id]).first()
    for name in ["label","field_type","placeholder","is_required","validation_config"]:
        value = getattr(field_in, name)
        if value is not None:
            setattr(field, name, value)
    if field_in.options is not None:
        field.options.clear()
        for opt in field_in.options:
            field.options.append(FieldOption(option_label=opt.option_label, option_value=opt.option_value,
                                             display_order=opt.display_order))
    form.status = "draft"; form.updated_at = datetime.utcnow()
    db.commit(); db.refresh(field); return field

def remove_field(db: Session, field_id: uuid.UUID, user_id: uuid.UUID) -> None:
    field = db.query(Field).join(FormVersion).join(Form).filter(Field.id == field_id, Form.created_by == user_id).first()
    if not field: raise HTTPException(status_code=404, detail="Field not found")
    form = field.form_version.form
    if form.status == "archived": raise HTTPException(status_code=400, detail="Archived forms cannot be edited")
    if field.form_version.is_active:
        raise HTTPException(status_code=400, detail="Published versions are immutable; edit the form to create a draft first.")
    db.delete(field); form.status = "draft"; form.updated_at = datetime.utcnow()
    db.commit()

def reorder_fields(db: Session, form_id: uuid.UUID, reorder_in: ReorderFieldsRequest, user_id: uuid.UUID) -> list[Field]:
    form = get_form_or_404(db, form_id, user_id)
    if form.status == "archived": raise HTTPException(status_code=400, detail="Archived forms cannot be edited")
    draft = _get_or_create_draft_version(db, form)
    ids = {f.id for f in draft.fields}
    if {x.field_id for x in reorder_in.order} - ids:
        raise HTTPException(status_code=400, detail="One or more fields do not belong to the current draft")
    for item in reorder_in.order:
        db.query(Field).filter(Field.id == item.field_id).update({"display_order": item.display_order})
    form.status = "draft"; form.updated_at = datetime.utcnow()
    db.commit()
    return sorted(db.query(Field).filter(Field.form_version_id == draft.id).all(), key=lambda f: f.display_order)

def add_rule(db: Session, form_id: uuid.UUID, rule_in: ConditionalRuleCreate, user_id: uuid.UUID) -> ConditionalRule:
    form = get_form_or_404(db, form_id, user_id)
    if form.status == "archived": raise HTTPException(status_code=400, detail="Archived forms cannot be edited")
    draft = _get_or_create_draft_version(db, form)
    trigger = db.query(Field).filter(Field.id == rule_in.trigger_field_id, Field.form_version_id == draft.id).first()
    target = db.query(Field).filter(Field.id == rule_in.target_field_id, Field.form_version_id == draft.id).first()
    if not trigger or not target: raise HTTPException(status_code=400, detail="Trigger and target must be fields in the current draft")
    rule = ConditionalRule(trigger_field_id=trigger.id, target_field_id=target.id, operator=rule_in.operator,
                           comparison_value=rule_in.comparison_value, action=rule_in.action)
    db.add(rule); form.status="draft"; form.updated_at=datetime.utcnow()
    db.commit(); db.refresh(rule); return rule

def list_rules(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> list[ConditionalRule]:
    form = get_form_or_404(db, form_id, user_id); version = _latest_version(db, form)
    if not version: return []
    ids=[f.id for f in version.fields]
    return db.query(ConditionalRule).filter(ConditionalRule.trigger_field_id.in_(ids), ConditionalRule.target_field_id.in_(ids)).all()

def delete_rule(db: Session, rule_id: uuid.UUID, user_id: uuid.UUID) -> None:
    rule = db.query(ConditionalRule).join(Field, ConditionalRule.trigger_field_id == Field.id).join(
        FormVersion, Field.form_version_id == FormVersion.id).join(Form, FormVersion.form_id == Form.id
    ).filter(ConditionalRule.id == rule_id, Form.created_by == user_id).first()
    if not rule: raise HTTPException(status_code=404, detail="Rule not found")
    if rule.trigger_field.form_version.is_active: raise HTTPException(status_code=400, detail="Published versions are immutable")
    db.delete(rule); db.commit()

def publish_form(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> FormVersion:
    form = get_form_or_404(db, form_id, user_id)
    if form.status == "archived": raise HTTPException(status_code=400, detail="Cannot publish an archived form")
    latest = _latest_version(db, form)
    if not latest or not latest.fields: raise HTTPException(status_code=400, detail="Add at least one field before publishing")
    if latest.is_active: raise HTTPException(status_code=400, detail="This form has no unpublished changes to publish")
    db.query(FormVersion).filter(FormVersion.form_id == form.id, FormVersion.is_active == True).update({"is_active": False})
    latest.is_active=True; latest.published_at=datetime.utcnow(); form.status="published"; form.updated_at=datetime.utcnow()
    db.commit(); db.refresh(latest); return latest

def get_versions(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> list[FormVersion]:
    form=get_form_or_404(db, form_id, user_id)
    return db.query(FormVersion).filter(FormVersion.form_id==form.id).order_by(FormVersion.version_number.desc()).all()

def get_version_detail(db: Session, form_id: uuid.UUID, version_number: int, user_id: uuid.UUID) -> FormVersion:
    form=get_form_or_404(db, form_id, user_id)
    v=db.query(FormVersion).filter(FormVersion.form_id==form.id, FormVersion.version_number==version_number).first()
    if not v: raise HTTPException(status_code=404, detail="Version not found")
    return v

def generate_link(db: Session, form_id: uuid.UUID, user_id: uuid.UUID) -> FormShareLink:
    form=get_form_or_404(db, form_id, user_id)
    if form.status!="published": raise HTTPException(status_code=400, detail="Only published forms can be shared")
    active=db.query(FormVersion).filter(FormVersion.form_id==form.id, FormVersion.is_active==True).first()
    if not active: raise HTTPException(status_code=400, detail="No published version found")
    existing=db.query(FormShareLink).filter(FormShareLink.form_version_id==active.id).first()
    if existing: return existing
    link=FormShareLink(form_version_id=active.id, slug=secrets.token_urlsafe(8))
    db.add(link); db.commit(); db.refresh(link); return link

def get_public_form(db: Session, slug: str) -> FormVersion:
    link=db.query(FormShareLink).filter(FormShareLink.slug==slug).first()
    if not link: raise HTTPException(status_code=404, detail="Invalid link")
    v=link.form_version; form=v.form
    if form.status=="archived": raise HTTPException(status_code=410, detail="This form has been archived and is no longer available")
    if not v.is_active: raise HTTPException(status_code=410, detail="This link points to an outdated version")
    return v

def submit_public_form(db: Session, slug: str, data: SubmissionCreate) -> Submission:
    version=get_public_form(db, slug)
    fields={str(f.id): f for f in version.fields}
    # Enforce required fields and ignore unknown/admin data.
    for fid, field in fields.items():
        value=data.values.get(fid)
        if field.is_required and (value is None or value == "" or value == []):
            raise HTTPException(status_code=422, detail=f"{field.label} is required")
        if value is not None:
            if field.field_type == "email" and "@" not in str(value):
                raise HTTPException(status_code=422, detail=f"Invalid email for {field.label}")
            cfg=field.validation_config or {}
            if isinstance(value, (int,float)) and cfg.get("min") is not None and value < cfg["min"]:
                raise HTTPException(status_code=422, detail=f"{field.label} is below the minimum")
            if isinstance(value, (int,float)) and cfg.get("max") is not None and value > cfg["max"]:
                raise HTTPException(status_code=422, detail=f"{field.label} is above the maximum")
    submission=Submission(form_version_id=version.id, completion_time_seconds=data.completion_time_seconds)
    db.add(submission); db.flush()
    for fid, value in data.values.items():
        if fid not in fields: continue
        db.add(ResponseValue(submission_id=submission.id, field_id=fields[fid].id,
                              value=json_value(value)))
    db.commit(); db.refresh(submission); return submission

def json_value(value):
    import json
    return json.dumps(value) if isinstance(value,(dict,list)) else str(value)
