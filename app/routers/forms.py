"""Task 4: Form Management; Task 5: Versioning/Publishing; Task 6: Shareable Access."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.auth import get_current_user
from app.schemas.form import (
    FormCreate, FormUpdate, FormOut, FormDetailOut, FormListItem,
    FieldCreate, FieldUpdate, FieldOut, ReorderFieldsRequest,
    ConditionalRuleCreate, ConditionalRuleUpdate, ConditionalRuleOut,
    FormVersionOut, FormVersionDetailOut, ShareLinkOut, PublicFormOut,
    SubmissionCreate, SubmissionOut,
)
from app.services import form_service

forms_router=APIRouter(prefix="/forms", tags=["forms"])
fields_router=APIRouter(prefix="/fields", tags=["fields"])
public_router=APIRouter(prefix="/public/forms", tags=["public"])

def _detail(form, version):
    return FormDetailOut(
        **FormOut.model_validate(form).model_dump(),
        fields=[FieldOut.model_validate(f) for f in sorted(version.fields,key=lambda x:x.display_order)] if version else [],
        editing_version_number=version.version_number if version else 0,
    )

@forms_router.post("",response_model=FormOut,status_code=status.HTTP_201_CREATED)
def create_form(body:FormCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.create_form(db,body,current_user.id)

@forms_router.get("",response_model=list[FormListItem])
def list_forms(db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    from app.models.form import Form
    return db.query(Form).filter(Form.created_by==current_user.id).order_by(Form.updated_at.desc()).all()

@forms_router.get("/{form_id}",response_model=FormDetailOut)
def get_form(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return _detail(*form_service.get_form_with_fields(db,form_id,current_user.id))

@forms_router.put("/{form_id}",response_model=FormOut)
def update_form(form_id:uuid.UUID,body:FormUpdate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.update_form(db,form_id,body,current_user.id)

@forms_router.patch("/{form_id}/archive",response_model=FormOut)
def archive_form(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.archive_form(db,form_id,current_user.id)

@forms_router.post("/{form_id}/fields",response_model=FieldOut,status_code=201)
def add_field(form_id:uuid.UUID,body:FieldCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.add_field(db,form_id,body,current_user.id)

@forms_router.patch("/{form_id}/reorder-fields",response_model=list[FieldOut])
def reorder(form_id:uuid.UUID,body:ReorderFieldsRequest,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.reorder_fields(db,form_id,body,current_user.id)

@fields_router.put("/{field_id}",response_model=FieldOut)
def update_field(field_id:uuid.UUID,body:FieldUpdate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.update_field(db,field_id,body,current_user.id)

@fields_router.delete("/{field_id}",status_code=204)
def delete_field(field_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    form_service.remove_field(db,field_id,current_user.id)

@forms_router.post("/{form_id}/rules",response_model=ConditionalRuleOut,status_code=201)
def add_rule(form_id:uuid.UUID,body:ConditionalRuleCreate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.add_rule(db,form_id,body,current_user.id)

@forms_router.get("/{form_id}/rules",response_model=list[ConditionalRuleOut])
def rules(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.list_rules(db,form_id,current_user.id)

@forms_router.delete("/rules/{rule_id}",status_code=204)
def delete_rule(rule_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    form_service.delete_rule(db,rule_id,current_user.id)

@forms_router.post("/{form_id}/publish",response_model=FormVersionOut)
def publish(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.publish_form(db,form_id,current_user.id)

@forms_router.get("/{form_id}/versions",response_model=list[FormVersionOut])
def versions(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    return form_service.get_versions(db,form_id,current_user.id)

@forms_router.get("/{form_id}/versions/{version_number}",response_model=FormVersionDetailOut)
def version_detail(form_id:uuid.UUID,version_number:int,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    v=form_service.get_version_detail(db,form_id,version_number,current_user.id)
    ids=[f.id for f in v.fields]
    from app.models.conditional_rule import ConditionalRule
    rs=db.query(ConditionalRule).filter(ConditionalRule.trigger_field_id.in_(ids),ConditionalRule.target_field_id.in_(ids)).all() if ids else []
    return FormVersionDetailOut(**FormVersionOut.model_validate(v).model_dump(),
        fields=[FieldOut.model_validate(f) for f in sorted(v.fields,key=lambda x:x.display_order)],
        rules=rs)

@forms_router.post("/{form_id}/generate-link",response_model=ShareLinkOut)
def generate_link(form_id:uuid.UUID,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    link=form_service.generate_link(db,form_id,current_user.id)
    return ShareLinkOut(slug=link.slug,public_url=f"/public/forms/{link.slug}",form_version_number=link.form_version.version_number)

@public_router.get("/{slug}",response_model=PublicFormOut)
def public_form(slug:str,db:Session=Depends(get_db)):
    v=form_service.get_public_form(db,slug)
    ids=[f.id for f in v.fields]
    from app.models.conditional_rule import ConditionalRule
    rs=db.query(ConditionalRule).filter(ConditionalRule.trigger_field_id.in_(ids),ConditionalRule.target_field_id.in_(ids)).all() if ids else []
    return PublicFormOut(title=v.form.title,description=v.form.description,
                         fields=sorted(v.fields,key=lambda x:x.display_order),rules=rs)

@public_router.post("/{slug}/submit",response_model=SubmissionOut,status_code=201)
def submit(slug:str,body:SubmissionCreate,db:Session=Depends(get_db)):
    s=form_service.submit_public_form(db,slug,body)
    return SubmissionOut(response_id=s.response_id,submitted_at=s.submitted_at,message="Response submitted successfully")

@forms_router.put("/rules/{rule_id}",response_model=ConditionalRuleOut)
def update_rule(rule_id:uuid.UUID,body:ConditionalRuleUpdate,db:Session=Depends(get_db),current_user=Depends(get_current_user)):
    from app.models.conditional_rule import ConditionalRule
    rule=db.query(ConditionalRule).join(Field,ConditionalRule.trigger_field_id==Field.id).join(FormVersion,Field.form_version_id==FormVersion.id).join(Form,FormVersion.form_id==Form.id).filter(ConditionalRule.id==rule_id,Form.created_by==current_user.id).first()
    if not rule:
        raise HTTPException(status_code=404,detail="Rule not found")
    if rule.trigger_field.form_version.is_active:
        raise HTTPException(status_code=400,detail="Published versions are immutable")
    if body.operator is not None:
        rule.operator=body.operator
    if body.comparison_value is not None:
        rule.comparison_value=body.comparison_value
    if body.target_field_id is not None:
        rule.target_field_id=body.target_field_id
    if body.action is not None:
        rule.action=body.action
    db.commit();db.refresh(rule)
    return rule