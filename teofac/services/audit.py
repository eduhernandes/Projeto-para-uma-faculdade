import json
from flask import request
from ..extensions import db
from ..models import AuditLog, utcnow

def audit(actor_id,action,entity_type=None,entity_id=None,details=None):
    entry=AuditLog(actor_id=actor_id,action=action,entity_type=entity_type,entity_id=entity_id,details=json.dumps(details,ensure_ascii=False,default=str) if details is not None else None,ip_address=(request.remote_addr),user_agent=(request.user_agent.string[:500] if request.user_agent else None),created_at=utcnow())
    db.session.add(entry); db.session.commit()


def log_event(action, entity_type=None, entity_id=None, details=None):
    from flask import g
    actor_id = getattr(g.get("current_user"), "id", None)
    audit(actor_id, action, entity_type, entity_id, details)
