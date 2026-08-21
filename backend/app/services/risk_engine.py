"""
Risk Engine
===========
The single source of truth for all risk math. Nothing about risk is
computed in the frontend - React only renders numbers this module produces.

Flow:
    Answer (option.risk_score) x Question.weight  -> Question Risk
    Sum of Question Risk for questions mapped to a node -> Node Risk
    Sum/aggregate of node scores under a category -> Category Risk
    Aggregate of category scores -> Overall Assessment Risk

Risk level bands are read from the `risk_thresholds` table so they are
configurable by an admin instead of hard-coded.
"""
from typing import Dict, List
from sqlalchemy.orm import Session

from app.models.assessment import Answer, Assessment, AssessmentResult
from app.models.question import QuestionMapping
from app.models.linddun import LinddunCategory, LinddunNode, RiskThreshold

DEFAULT_THRESHOLDS = [
    ("LOW", 0, 20),
    ("MEDIUM", 21, 40),
    ("HIGH", 41, 60),
    ("CRITICAL", 61, 10_000),
]


def get_risk_level(db: Session, score: float) -> str:
    thresholds = db.query(RiskThreshold).order_by(RiskThreshold.display_order).all()
    bands = (
        [(t.level_name, t.min_score, t.max_score) for t in thresholds]
        if thresholds
        else DEFAULT_THRESHOLDS
    )
    for level, lo, hi in bands:
        if lo <= score <= hi:
            return level
    return bands[-1][0]


def compute_question_score(answer: Answer) -> float:
    """Question Risk = Answer Score x Question Weight"""
    if answer.selected_option is None:
        return 0.0
    weight = answer.question.weight or 1.0
    return round(answer.selected_option.risk_score * weight, 2)


def calculate_assessment_risk(db: Session, assessment: Assessment) -> Dict:
    """
    Recompute every answer's score, then roll scores up:
    answers -> node scores -> category scores -> overall score.
    Persists AssessmentResult rows (one per category, one per node)
    and updates Assessment.overall_score / overall_risk_level.
    Returns a summary dict used by the API layer.
    """
    answers: List[Answer] = (
        db.query(Answer).filter(Answer.assessment_id == assessment.id).all()
    )

    # 1. Recompute each answer's score and persist.
    for ans in answers:
        ans.computed_score = compute_question_score(ans)
    db.flush()

    # 2. Aggregate per node: sum the scores of all answers whose question
    #    maps to that node.
    node_scores: Dict[str, float] = {}
    node_question_counts: Dict[str, int] = {}
    for ans in answers:
        mappings = (
            db.query(QuestionMapping)
            .filter(QuestionMapping.question_id == ans.question_id)
            .all()
        )
        for m in mappings:
            if m.node_id:
                key = str(m.node_id)
                node_scores[key] = node_scores.get(key, 0) + ans.computed_score
                node_question_counts[key] = node_question_counts.get(key, 0) + 1

    # 3. Aggregate per category: sum of (a) node scores under it and
    #    (b) any answers mapped directly to the category with no node.
    category_scores: Dict[str, float] = {}
    for ans in answers:
        mappings = (
            db.query(QuestionMapping)
            .filter(QuestionMapping.question_id == ans.question_id)
            .all()
        )
        for m in mappings:
            key = str(m.category_id)
            category_scores[key] = category_scores.get(key, 0) + ans.computed_score

    # 4. Clear old results for this assessment, write fresh ones.
    db.query(AssessmentResult).filter(AssessmentResult.assessment_id == assessment.id).delete()

    for cat_id, score in category_scores.items():
        db.add(
            AssessmentResult(
                assessment_id=assessment.id,
                category_id=cat_id,
                node_id=None,
                score=score,
                risk_level=get_risk_level(db, score),
            )
        )
    for node_id, score in node_scores.items():
        db.add(
            AssessmentResult(
                assessment_id=assessment.id,
                category_id=None,
                node_id=node_id,
                score=score,
                risk_level=get_risk_level(db, score),
            )
        )

    # 5. Overall assessment risk = sum of all category risk scores.
    #    Kept as a simple, transparent aggregation so the banding in
    #    risk_thresholds stays meaningful and auditable.
    overall_score = round(sum(category_scores.values()), 2)
    overall_level = get_risk_level(db, overall_score)

    assessment.overall_score = overall_score
    assessment.overall_risk_level = overall_level

    db.commit()

    return {
        "overall_score": overall_score,
        "overall_risk_level": overall_level,
        "category_scores": category_scores,
        "node_scores": node_scores,
    }
