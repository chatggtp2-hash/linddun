"""
Tree Engine
===========
Builds the hierarchical LINDDUN threat tree entirely from database state.
Nothing is hand-drawn: the shape of the tree comes from linddun_categories /
linddun_nodes (parent_id self-reference), and the risk numbers annotated on
each node come from the most recent AssessmentResult rows (which the Risk
Engine produced). If an assessment_id is not supplied, the tree is returned
with the framework structure only (score 0 / risk "NONE"), which is what the
admin's "Manage LINDDUN Tree" screen uses.
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session

from app.models.linddun import LinddunCategory, LinddunNode
from app.models.assessment import AssessmentResult
from app.models.question import QuestionMapping
from app.models.evidence import Evidence


def _question_counts(db: Session) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for m in db.query(QuestionMapping).all():
        if m.node_id:
            key = str(m.node_id)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _evidence_counts(db: Session, assessment_id: Optional[str]) -> Dict[str, int]:
    q = db.query(Evidence)
    if assessment_id:
        q = q.filter(Evidence.assessment_id == assessment_id)
    counts: Dict[str, int] = {}
    for e in q.all():
        if e.node_id:
            key = str(e.node_id)
            counts[key] = counts.get(key, 0) + 1
    return counts


def _build_node(node: LinddunNode, all_children: Dict, node_scores: Dict, q_counts: Dict, ev_counts: Dict) -> dict:
    key = str(node.id)
    score = node_scores.get(key, 0)
    risk = _score_to_level(score) if key in node_scores else "NONE"
    children = [
        _build_node(child, all_children, node_scores, q_counts, ev_counts)
        for child in sorted(all_children.get(key, []), key=lambda n: n.display_order)
    ]
    return {
        "id": key,
        "code": node.code,
        "name": node.name,
        "risk": risk,
        "score": score,
        "question_count": q_counts.get(key, 0),
        "evidence_count": ev_counts.get(key, 0),
        "children": children,
    }


def _score_to_level(score: float) -> str:
    # mirrors default bands; admin-configurable version lives in risk_engine
    if score <= 20:
        return "LOW"
    if score <= 40:
        return "MEDIUM"
    if score <= 60:
        return "HIGH"
    return "CRITICAL"


def build_category_tree(db: Session, category: LinddunCategory, assessment_id: Optional[str] = None) -> dict:
    nodes = db.query(LinddunNode).filter(
        LinddunNode.category_id == category.id, LinddunNode.is_active == True  # noqa: E712
    ).all()

    all_children: Dict[str, list] = {}
    roots = []
    for n in nodes:
        if n.parent_id:
            all_children.setdefault(str(n.parent_id), []).append(n)
        else:
            roots.append(n)

    node_scores: Dict[str, float] = {}
    if assessment_id:
        results = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.assessment_id == assessment_id, AssessmentResult.node_id.isnot(None))
            .all()
        )
        for r in results:
            node_scores[str(r.node_id)] = r.score

    q_counts = _question_counts(db)
    ev_counts = _evidence_counts(db, assessment_id)

    category_score = 0.0
    category_risk = "NONE"
    if assessment_id:
        cat_result = (
            db.query(AssessmentResult)
            .filter(AssessmentResult.assessment_id == assessment_id, AssessmentResult.category_id == category.id)
            .first()
        )
        if cat_result:
            category_score = cat_result.score
            category_risk = cat_result.risk_level

    return {
        "id": str(category.id),
        "code": category.code,
        "name": category.name,
        "risk": category_risk,
        "score": category_score,
        "question_count": sum(q_counts.get(str(n.id), 0) for n in nodes),
        "evidence_count": sum(ev_counts.get(str(n.id), 0) for n in nodes),
        "children": [
            _build_node(root, all_children, node_scores, q_counts, ev_counts)
            for root in sorted(roots, key=lambda n: n.display_order)
        ],
    }


def build_full_tree(db: Session, assessment_id: Optional[str] = None) -> list:
    """Returns a list of category trees, one per active LINDDUN category."""
    categories = (
        db.query(LinddunCategory)
        .filter(LinddunCategory.is_active == True)  # noqa: E712
        .order_by(LinddunCategory.display_order)
        .all()
    )
    return [build_category_tree(db, c, assessment_id) for c in categories]
