"""
Import every model here so that Base.metadata is fully populated —
this is what alembic/env.py relies on for `alembic revision --autogenerate`.
"""
from app.models.user import User               # noqa: F401
from app.models.form import Form                # noqa: F401
from app.models.form_version import FormVersion  # noqa: F401
from app.models.field import Field               # noqa: F401
from app.models.field_option import FieldOption  # noqa: F401
from app.models.conditional_rule import ConditionalRule  # noqa: F401
from app.models.submission import Submission     # noqa: F401
from app.models.response_value import ResponseValue  # noqa: F401
from app.models.form_share_link import FormShareLink  # noqa: F401
from app.models.uploaded_file import UploadedFile  # noqa: F401
