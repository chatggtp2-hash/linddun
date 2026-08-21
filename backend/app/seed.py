"""
Seed data for the LINDDUN platform.
Run with:  python -m app.seed
Creates admin/assessor/reviewer users, the full 7-category hierarchical
LINDDUN tree (Non-repudiation matching the reference screenshot exactly),
demo questions mapped to threat nodes, risk thresholds, and recommendation
rules — so the app works immediately after `alembic upgrade head`.
"""
from app.database import SessionLocal, engine, Base
from app.middleware.auth import hash_password
from app.models.user import User, RoleEnum
from app.models.linddun import (
    FrameworkVersion, LinddunCategory, LinddunNode, RiskThreshold, RecommendationRule
)
from app.models.question import Question, QuestionOption, QuestionMapping, QuestionType

import app.models  # noqa: F401 ensure all models are registered on Base


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        # ---------------- Users ----------------
        admin = User(email="admin@linddun-demo.com", full_name="Alex Admin",
                     hashed_password=hash_password("Admin@123"), role=RoleEnum.ADMIN)
        assessor = User(email="assessor@linddun-demo.com", full_name="Sam Assessor",
                         hashed_password=hash_password("Assessor@123"), role=RoleEnum.ASSESSOR)
        reviewer = User(email="reviewer@linddun-demo.com", full_name="Riya Reviewer",
                         hashed_password=hash_password("Reviewer@123"), role=RoleEnum.REVIEWER)
        db.add_all([admin, assessor, reviewer])
        db.flush()

        # ---------------- Framework version ----------------
        fw = FrameworkVersion(version_label="v1", is_active=True)
        db.add(fw)
        db.flush()

        # ---------------- Risk thresholds ----------------
        db.add_all([
            RiskThreshold(level_name="LOW", min_score=0, max_score=20, display_order=1),
            RiskThreshold(level_name="MEDIUM", min_score=21, max_score=40, display_order=2),
            RiskThreshold(level_name="HIGH", min_score=41, max_score=60, display_order=3),
            RiskThreshold(level_name="CRITICAL", min_score=61, max_score=100000, display_order=4),
        ])

        # ---------------- Categories ----------------
        cat_defs = [
            ("L", "Linkability", "Being able to link two or more items of interest to draw conclusions."),
            ("I", "Identifiability", "Being able to identify a data subject from a set of data."),
            ("NR", "Non-repudiation", "Data or actions being attributable to a specific data subject."),
            ("D", "Detectability", "Being able to deduce the existence of an item of interest."),
            ("DI", "Disclosure of information", "Excessive exposure of personal data to unauthorized parties."),
            ("U", "Unawareness", "Data subjects unaware of collection, processing, or sharing of their data."),
            ("NC", "Non-compliance", "Processing that deviates from legislation, regulation, and policy."),
        ]
        categories = {}
        for i, (code, name, desc) in enumerate(cat_defs):
            cat = LinddunCategory(
                code=code, name=name, description=desc, short_description=desc[:60],
                risk_definition=f"Risk that {name.lower()} threats compromise data subject privacy.",
                display_order=i, framework_version_id=fw.id,
            )
            db.add(cat)
            categories[code] = cat
        db.flush()

        nodes = {}

        def add_node(code, category_code, name, parent_code=None, order=0, desc=None, controls=None):
            node = LinddunNode(
                category_id=categories[category_code].id,
                parent_id=nodes[parent_code].id if parent_code else None,
                code=code, name=name, display_order=order,
                description=desc or f"{name} threat under {categories[category_code].name}.",
                recommended_controls=controls,
            )
            db.add(node)
            db.flush()
            nodes[code] = node
            return node

        # ---- Non-repudiation (reference structure from screenshot) ----
        add_node("NR-1", "NR", "Attributable data evidence", order=0,
                  controls="Minimize logging of attributable identifiers; use pseudonymous IDs where possible.")
        add_node("NR-2", "NR", "Attributable action side-effect evidence", order=1,
                  controls="Avoid side effects (timestamps, receipts) that can re-identify the actor.")
        add_node("NR-1-1", "NR", "Data", parent_code="NR-1", order=0)
        add_node("NR-1-2", "NR", "Signed data", parent_code="NR-1", order=1,
                  controls="Use group signatures or ring signatures to reduce attributability.")
        add_node("NR-1-3", "NR", "Metadata", parent_code="NR-1", order=2,
                  controls="Strip or generalize metadata (device IDs, IPs, timestamps) before storage.")
        add_node("NR-1-4", "NR", "Embedded/Hidden Data", parent_code="NR-1", order=3,
                  controls="Scan and strip steganographic or embedded identifiers from files.")

        # ---- Linkability ----
        add_node("L-1", "L", "Linkability of data subjects", order=0)
        add_node("L-2", "L", "Linkability of datasets", order=1)
        add_node("L-1-1", "L", "Identifiers reused across contexts", parent_code="L-1", order=0,
                  controls="Use context-specific pseudonymous identifiers instead of shared IDs.")
        add_node("L-1-2", "L", "Behavioral/quasi-identifier correlation", parent_code="L-1", order=1,
                  controls="Apply k-anonymity/differential privacy to behavioral datasets.")
        add_node("L-2-1", "L", "Cross-system dataset joins", parent_code="L-2", order=0,
                  controls="Restrict joins on common keys; enforce data minimization agreements.")

        # ---- Identifiability ----
        add_node("I-1", "I", "Direct identification", order=0,
                  controls="Remove or mask direct identifiers (name, SSN, national ID).")
        add_node("I-2", "I", "Indirect identification", order=1,
                  controls="Apply generalization/suppression to quasi-identifiers.")
        add_node("I-1-1", "I", "Explicit identifiers in storage", parent_code="I-1", order=0)
        add_node("I-2-1", "I", "Re-identification via auxiliary data", parent_code="I-2", order=0,
                  controls="Conduct re-identification risk assessments before release.")

        # ---- Detectability ----
        add_node("D-1", "D", "Detectable data existence", order=0,
                  controls="Use encryption/padding so presence of records isn't inferable from traffic.")
        add_node("D-2", "D", "Detectable communication patterns", order=1,
                  controls="Apply traffic padding or mixing to obscure communication timing/size.")
        add_node("D-1-1", "D", "File/record size fingerprinting", parent_code="D-1", order=0)

        # ---- Disclosure of information ----
        add_node("DI-1", "DI", "Excessive data exposure", order=0,
                  controls="Review access controls, encryption, data sharing mechanisms, and third-party transfers.")
        add_node("DI-2", "DI", "Unauthorized third-party access", order=1,
                  controls="Enforce least-privilege access and vendor data processing agreements.")
        add_node("DI-1-1", "DI", "Over-broad API responses", parent_code="DI-1", order=0,
                  controls="Apply field-level filtering/response minimization on APIs.")

        # ---- Unawareness ----
        add_node("U-1", "U", "Lack of transparency", order=0,
                  controls="Publish clear, accessible privacy notices at point of collection.")
        add_node("U-2", "U", "Lack of consent/control", order=1,
                  controls="Provide granular consent and data subject rights (access, deletion, portability).")
        add_node("U-1-1", "U", "No notice at collection point", parent_code="U-1", order=0)

        # ---- Non-compliance ----
        add_node("NC-1", "NC", "Regulatory non-compliance", order=0,
                  controls="Map processing activities against applicable regulations (GDPR, DPDP, etc.).")
        add_node("NC-2", "NC", "Policy non-compliance", order=1,
                  controls="Align internal data handling with documented organizational policy.")
        add_node("NC-1-1", "NC", "Missing legal basis for processing", parent_code="NC-1", order=0)

        db.flush()

        # ---------------- Recommendation rules ----------------
        db.add_all([
            RecommendationRule(category_id=categories["DI"].id, trigger_risk_level="HIGH",
                                recommendation_text="Review access controls, encryption, data sharing mechanisms, and third-party data transfers."),
            RecommendationRule(category_id=categories["L"].id, trigger_risk_level="HIGH",
                                recommendation_text="Review dataset correlation, identifiers, pseudonymous identifiers, and unnecessary data linkage."),
            RecommendationRule(category_id=categories["I"].id, trigger_risk_level="HIGH",
                                recommendation_text="Review direct and indirect identifiers and strengthen data minimization and pseudonymization."),
            RecommendationRule(category_id=categories["NR"].id, trigger_risk_level="MEDIUM",
                                recommendation_text="Assess whether attributable evidence (metadata, signatures) is broader than necessary."),
            RecommendationRule(category_id=categories["D"].id, trigger_risk_level="HIGH",
                                recommendation_text="Apply traffic and storage obfuscation to reduce detectability of sensitive records."),
            RecommendationRule(category_id=categories["U"].id, trigger_risk_level="MEDIUM",
                                recommendation_text="Improve transparency notices and consent mechanisms for data subjects."),
            RecommendationRule(category_id=categories["NC"].id, trigger_risk_level="MEDIUM",
                                recommendation_text="Conduct a compliance gap analysis against applicable privacy regulations."),
        ])

        # ---------------- Demo questions (cover all 7 categories) ----------------
        def add_question(text, category_code, node_code, weight=1.0, order=0, help_text=None, invert_risk=False):
            q = Question(text=text, help_text=help_text, question_type=QuestionType.YES_NO,
                          weight=weight, display_order=order, is_mandatory=True, created_by=admin.id)
            db.add(q)
            db.flush()
            yes_score, no_score = (1, 5) if invert_risk else (5, 1)
            yes_level, no_level = ("LOW", "HIGH") if invert_risk else ("HIGH", "LOW")
            db.add(QuestionOption(question_id=q.id, label="Yes", value="YES", risk_score=yes_score, risk_level=yes_level, display_order=0))
            db.add(QuestionOption(question_id=q.id, label="No", value="NO", risk_score=no_score, risk_level=no_level, display_order=1))
            db.add(QuestionMapping(question_id=q.id, category_id=categories[category_code].id,
                                    node_id=nodes[node_code].id if node_code else None))
            return q

        add_question("Can customer records be linked across multiple systems?", "L", "L-2-1", order=1)
        add_question("Can a specific individual be identified from the available data?", "I", "I-1-1", order=2)
        add_question("Can activity performed by a user be attributed to that specific user?", "NR", "NR-1-3",
                      order=3, help_text="Consider logs, signed transactions, or embedded metadata.")
        add_question("Can the existence of a specific record be inferred without accessing its content?", "D", "D-1-1", order=4)
        add_question("Is personal data combined with another dataset that can identify the same person?", "L", "L-1-1", order=5)
        add_question("Is data shared with third parties without explicit access restrictions?", "DI", "DI-1-1", order=6)
        add_question("Are data subjects clearly informed about how their data is collected and used?", "U", "U-1-1",
                      order=7, help_text="Answering NO indicates a transparency gap (higher risk).", invert_risk=True)
        add_question("Is there a documented legal basis for this processing activity?", "NC", "NC-1-1",
                      order=8, help_text="Answering NO indicates a compliance gap (higher risk).", invert_risk=True)

        db.commit()
        print("Seed complete.")
        print("Login credentials:")
        print("  Admin:    admin@linddun-demo.com / Admin@123")
        print("  Assessor: assessor@linddun-demo.com / Assessor@123")
        print("  Reviewer: reviewer@linddun-demo.com / Reviewer@123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
