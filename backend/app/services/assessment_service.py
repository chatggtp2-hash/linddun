from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_audit(
    db: Session,
    user_id,
    action: str,
    entity: str,
    entity_id: str = None,
    ip_address: str = None,
    previous_value: str = None,
    new_value: str = None,
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=str(entity_id) if entity_id else None,
        ip_address=ip_address,
        previous_value=previous_value,
        new_value=new_value,
    )
    db.add(entry)
    db.commit()
