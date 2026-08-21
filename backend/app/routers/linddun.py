import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.permissions import require_admin, require_any
from app.models.linddun import LinddunCategory, LinddunNode
from app.models.user import User
from app.schemas.linddun import LinddunCategoryOut, LinddunNodeCreate, LinddunNodeUpdate, LinddunNodeOut
from app.services.tree_engine import build_full_tree
from app.services.assessment_service import log_audit

router = APIRouter(prefix="/api/linddun", tags=["linddun"])


@router.get("/categories", response_model=list[LinddunCategoryOut])
def list_categories(db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    return db.query(LinddunCategory).filter(LinddunCategory.is_active == True).order_by(LinddunCategory.display_order).all()  # noqa: E712


@router.get("/tree")
def get_full_tree(assessment_id: uuid.UUID | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    return build_full_tree(db, str(assessment_id) if assessment_id else None)


@router.get("/nodes", response_model=list[LinddunNodeOut])
def list_nodes(category_id: uuid.UUID | None = None, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    q = db.query(LinddunNode)
    if category_id:
        q = q.filter(LinddunNode.category_id == category_id)
    return q.order_by(LinddunNode.display_order).all()


@router.post("/nodes", response_model=LinddunNodeOut)
def create_node(payload: LinddunNodeCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    node = LinddunNode(**payload.dict())
    db.add(node)
    db.commit()
    db.refresh(node)
    log_audit(db, current_user.id, "LINDDUN_NODE_CREATED", "linddun_node", node.id, new_value=node.name)
    return node


@router.put("/nodes/{node_id}", response_model=LinddunNodeOut)
def update_node(node_id: uuid.UUID, payload: LinddunNodeUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    node = db.query(LinddunNode).filter(LinddunNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Node not found", "error_code": "NODE_NOT_FOUND"})
    old_name = node.name
    for k, v in payload.dict(exclude_unset=True).items():
        setattr(node, k, v)
    db.commit()
    log_audit(db, current_user.id, "LINDDUN_NODE_UPDATED", "linddun_node", node.id, previous_value=old_name, new_value=node.name)
    return node
