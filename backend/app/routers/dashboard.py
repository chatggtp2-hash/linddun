from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.permissions import require_any, require_admin
from app.models.assessment import Assessment, AssessmentStatus, AssessmentResult
from app.models.linddun import LinddunCategory
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

audit_router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@audit_router.get("")
def list_audit_logs(limit: int = 200, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "ip_address": l.ip_address,
            "previous_value": l.previous_value,
            "new_value": l.new_value,
            "timestamp": l.timestamp,
        }
        for l in logs
    ]


@router.get("/summary")
def summary(db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessments = db.query(Assessment).all()
    total = len(assessments)
    completed = len([a for a in assessments if a.status == AssessmentStatus.COMPLETED])
    in_progress = len([a for a in assessments if a.status == AssessmentStatus.IN_PROGRESS])
    high_risk = len([a for a in assessments if a.overall_risk_level == "HIGH"])
    critical_risk = len([a for a in assessments if a.overall_risk_level == "CRITICAL"])

    completed_scores = [a.overall_score for a in assessments if a.overall_score is not None]
    avg_score = round(sum(completed_scores) / len(completed_scores), 2) if completed_scores else 0

    return {
        "total_assessments": total,
        "completed_assessments": completed,
        "in_progress_assessments": in_progress,
        "high_risk_assessments": high_risk,
        "critical_risk_assessments": critical_risk,
        "overall_risk_score": avg_score,
    }


@router.get("/risk-distribution")
def risk_distribution(db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessments = db.query(Assessment).filter(Assessment.overall_risk_level.isnot(None)).all()
    dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for a in assessments:
        if a.overall_risk_level in dist:
            dist[a.overall_risk_level] += 1
    return dist


@router.get("/linddun-risk")
def linddun_risk(db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    """Average risk score per LINDDUN category across all completed assessments."""
    categories = db.query(LinddunCategory).filter(LinddunCategory.is_active == True).order_by(LinddunCategory.display_order).all()  # noqa: E712
    out = []
    for cat in categories:
        results = db.query(AssessmentResult).filter(AssessmentResult.category_id == cat.id).all()
        scores = [r.score for r in results]
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        level = "LOW"
        if avg > 60:
            level = "CRITICAL"
        elif avg > 40:
            level = "HIGH"
        elif avg > 20:
            level = "MEDIUM"
        out.append({"category": cat.name, "code": cat.code, "score": avg, "risk_level": level})
    return sorted(out, key=lambda c: c["score"], reverse=True)
