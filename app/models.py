from datetime import datetime, timezone
from flask_login import UserMixin
from extensions import db


def utcnow():
    return datetime.now(timezone.utc)

class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(40), nullable=False, index=True)
    service = db.Column(db.String(160))
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin_approved = db.Column(db.Boolean, default=False, nullable=False)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime(timezone=True))
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)
    two_factor_secret = db.Column(db.String(64))
    email_token = db.Column(db.String(160), index=True)
    reset_token = db.Column(db.String(160), index=True)
    last_login_at = db.Column(db.DateTime(timezone=True))
    deleted_at = db.Column(db.DateTime(timezone=True))
    deleted_by_id = db.Column(db.Integer)
    delete_reason = db.Column(db.Text)
    deletion_requested_at = db.Column(db.DateTime(timezone=True))
    deletion_reason = db.Column(db.Text)
    deletion_confirmed_by_id = db.Column(db.Integer)
    deletion_confirmed_at = db.Column(db.DateTime(timezone=True))

class EcbuRequest(TimestampMixin, db.Model):
    __tablename__ = "ecbu_requests"
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    sampling_code = db.Column(db.String(80), index=True)
    patient_code = db.Column(db.String(80), index=True)
    patient_name = db.Column(db.String(120), nullable=False)
    patient_firstname = db.Column(db.String(160))
    patient_age = db.Column(db.String(20))
    patient_age_unit = db.Column(db.String(20))
    patient_sex = db.Column(db.String(20))
    patient_phone = db.Column(db.String(40))
    hospital_name = db.Column(db.String(180), index=True)
    origin_commune = db.Column(db.String(160), index=True)
    sample_nature = db.Column(db.String(80))
    patient_probe = db.Column(db.String(40))
    consultation_reason = db.Column(db.Text)
    general_signs = db.Column(db.Text)
    recent_hospitalization = db.Column(db.String(40))
    recent_hospitalization_duration = db.Column(db.String(80))
    currently_hospitalized = db.Column(db.String(40))
    current_hospitalization_duration = db.Column(db.String(80))
    antibiotic_treatment = db.Column(db.String(40))
    antibiotic_duration = db.Column(db.String(80))
    underlying_chronic_disease = db.Column(db.Text)
    main_diagnosis = db.Column(db.Text)
    sampling_date = db.Column(db.Date)
    requesting_service = db.Column(db.String(160), index=True)
    prescriber_name = db.Column(db.String(160))
    clinical_context = db.Column(db.Text)
    urgent = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(60), default="submitted", index=True)
    conformity = db.Column(db.String(40), default="not_evaluated", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_by = db.relationship("User")
    archived_at = db.Column(db.DateTime(timezone=True))
    deleted_at = db.Column(db.DateTime(timezone=True))

class Sample(TimestampMixin, db.Model):
    __tablename__ = "samples"
    id = db.Column(db.Integer, primary_key=True)
    sample_number = db.Column(db.String(60), unique=True, nullable=False, index=True)
    qr_code = db.Column(db.String(160), unique=True, nullable=False, index=True)
    request_id = db.Column(db.Integer, db.ForeignKey("ecbu_requests.id"), nullable=False)
    request = db.relationship("EcbuRequest", backref="samples")
    sample_type = db.Column(db.String(80))
    sampling_date = db.Column(db.Date)
    sampling_time = db.Column(db.Time)
    reception_date = db.Column(db.Date)
    reception_time = db.Column(db.Time)
    transport_condition = db.Column(db.String(160))
    storage_temperature = db.Column(db.String(80))
    status = db.Column(db.String(60), default="received", index=True)
    archived_at = db.Column(db.DateTime(timezone=True))

class QualityChecklist(TimestampMixin, db.Model):
    __tablename__ = "quality_checklists"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("ecbu_requests.id"), nullable=False, unique=True)
    request = db.relationship("EcbuRequest", backref="quality_checklist", uselist=False)
    patient_informed = db.Column(db.Boolean, default=False)
    technique_mastered = db.Column(db.Boolean, default=False)
    intimate_toilet = db.Column(db.Boolean, default=False)
    sterile_container = db.Column(db.Boolean, default=False)
    identified_container = db.Column(db.Boolean, default=False)
    sufficient_volume = db.Column(db.Boolean, default=False)
    no_leakage = db.Column(db.Boolean, default=False)
    delay_compliant = db.Column(db.Boolean, default=False)
    temperature_compliant = db.Column(db.Boolean, default=False)
    transport_compliant = db.Column(db.Boolean, default=False)
    sample_nature_compliant = db.Column(db.Boolean, default=False)
    decision = db.Column(db.String(40), default="not_evaluated")

class LabResult(TimestampMixin, db.Model):
    __tablename__ = "lab_results"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("ecbu_requests.id"), nullable=False, unique=True)
    request = db.relationship("EcbuRequest", backref="result", uselist=False)
    laboratory_name = db.Column(db.String(180))
    isolated_germ = db.Column(db.String(180))
    rejection_reason = db.Column(db.Text)
    aspect = db.Column(db.String(160))
    leukocytes = db.Column(db.String(80))
    red_cells = db.Column(db.String(80))
    epithelial_cells = db.Column(db.String(160))
    other_elements = db.Column(db.Text)
    gram_stain = db.Column(db.Text)
    culture_status = db.Column(db.String(80))
    culture_details = db.Column(db.Text)
    conclusion = db.Column(db.Text)
    validated_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    validated_at = db.Column(db.DateTime(timezone=True))
    electronic_signature = db.Column(db.String(160))
    deleted_at = db.Column(db.DateTime(timezone=True))
    deleted_by_id = db.Column(db.Integer)
    delete_reason = db.Column(db.Text)

class Antibiogram(TimestampMixin, db.Model):
    __tablename__ = "antibiograms"
    id = db.Column(db.Integer, primary_key=True)
    result_id = db.Column(db.Integer, db.ForeignKey("lab_results.id"), nullable=False)
    result = db.relationship("LabResult", backref="antibiograms")
    bacteria = db.Column(db.String(160), index=True)
    antibiotic = db.Column(db.String(160), nullable=False)
    diameter = db.Column(db.String(40))
    interpretation = db.Column(db.String(10), index=True)
    resistance_profile = db.Column(db.String(160))
    display_on_report = db.Column(db.Boolean, default=True)

class NonConformity(TimestampMixin, db.Model):
    __tablename__ = "non_conformities"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("ecbu_requests.id"))
    request = db.relationship("EcbuRequest", backref="non_conformities")
    type_nc = db.Column(db.String(120), nullable=False, index=True)
    severity = db.Column(db.String(40), index=True)
    impact = db.Column(db.String(80))
    consequence = db.Column(db.Text)
    decision = db.Column(db.Text)
    responsible = db.Column(db.String(160))
    status = db.Column(db.String(40), default="open", index=True)
    declared_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class CapaAction(TimestampMixin, db.Model):
    __tablename__ = "capa_actions"
    id = db.Column(db.Integer, primary_key=True)
    non_conformity_id = db.Column(db.Integer, db.ForeignKey("non_conformities.id"), nullable=False)
    non_conformity = db.relationship("NonConformity", backref="capa_actions")
    corrective_action = db.Column(db.Text)
    preventive_action = db.Column(db.Text)
    responsible = db.Column(db.String(160))
    due_date = db.Column(db.Date)
    effectiveness = db.Column(db.Text)
    status = db.Column(db.String(40), default="open", index=True)
    closed_at = db.Column(db.DateTime(timezone=True))

class Ticket(TimestampMixin, db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80))
    status = db.Column(db.String(40), default="open", index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(30), default="info")
    role_target = db.Column(db.String(40), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    seen_at = db.Column(db.DateTime(timezone=True))

class InternalMessage(TimestampMixin, db.Model):
    __tablename__ = "internal_messages"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("ecbu_requests.id"))
    request = db.relationship("EcbuRequest")
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipient_user = db.relationship("User", foreign_keys=[recipient_user_id])
    recipient_role = db.Column(db.String(40), index=True)
    subject = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text)
    seen_at = db.Column(db.DateTime(timezone=True))

class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(160))
    action = db.Column(db.String(160), nullable=False, index=True)
    entity_type = db.Column(db.String(80), index=True)
    entity_id = db.Column(db.String(80), index=True)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    ip_address = db.Column(db.String(80))
    hash_chain = db.Column(db.String(128), nullable=False)
