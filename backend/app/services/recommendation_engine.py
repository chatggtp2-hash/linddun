"""
Recommendation Engine
======================
Simple rule-based engine (no AI required for v1). Rules live in the
`recommendation_rules` table: (category_id or node_id) + trigger_risk_level
-> recommendation_text. This module matches an assessment's computed
category/node risk levels against active rules and returns the applicable
recommendation strings.
"""
from typing import List
from sqlalchemy.orm import Session

from app.models.linddun import RecommendationRule
from app.models.assessment import AssessmentResult

_LEVEL_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3, "NONE": -1}


def get_recommendations(db: Session, assessment_id: str) -> List[str]:
    results = db.query(AssessmentResult).filter(AssessmentResult.assessment_id == assessment_id).all()
    rules = db.query(RecommendationRule).filter(RecommendationRule.is_active == True).all()  # noqa: E712

    recommendations: List[str] = []
    seen = set()

    for result in results:
        for rule in rules:
            if rule.category_id and result.category_id and str(rule.category_id) != str(result.category_id):
                continue
            if rule.node_id and result.node_id and str(rule.node_id) != str(result.node_id):
                continue
            if rule.category_id and not result.category_id:
                continue
            if rule.node_id and not result.node_id:
                continue
            if not rule.category_id and not rule.node_id:
                continue

            actual_rank = _LEVEL_RANK.get(result.risk_level, -1)
            trigger_rank = _LEVEL_RANK.get(rule.trigger_risk_level, 99)
            if actual_rank >= trigger_rank and rule.recommendation_text not in seen:
                recommendations.append(rule.recommendation_text)
                seen.add(rule.recommendation_text)

    return recommendations
