"""Append-only audit log. Every state change goes through record_action."""
from sqlmodel import Session, select

from core.models import Action


def record_action(session: Session, entity_type: str, entity_id: int, action: str, detail: str = "") -> Action:
    entry = Action(entity_type=entity_type, entity_id=entity_id, action=action, detail=detail)
    session.add(entry)
    return entry


def actions_for(session: Session, entity_type: str, entity_id: int) -> list[Action]:
    stmt = (
        select(Action)
        .where(Action.entity_type == entity_type, Action.entity_id == entity_id)
        .order_by(Action.created_at)
    )
    return list(session.exec(stmt))
