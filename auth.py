import hashlib, secrets
from datetime import timedelta
from flask import flash, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from ..extensions import db
from ..models import PasswordResetToken, User, utcnow
from .audit import audit

def normalize_identifier(v): return v.strip().lower()
def hash_user_agent(): return hashlib.sha256((request.user_agent.string or '').encode('utf-8','ignore')).hexdigest()
def authenticate(identifier,password):
    ident=normalize_identifier(identifier)
    user=db.session.execute(db.select(User).where((User.username==ident)|(User.email==ident))).scalar_one_or_none()
    valid=user is not None and user.check_password(password)
    if not valid:
        audit(user.id if user else None,'login_failed','user',user.id if user else None); return None
    if not user.is_active:
        audit(user.id,'login_blocked_inactive','user',user.id); return None
    return user
def login_user(user):
    session.clear(); session.permanent=True; session['user_id']=user.id; session['session_version']=user.session_version; session['ua_hash']=hash_user_agent(); session['issued_at']=utcnow().isoformat(); user.last_login_at=utcnow(); db.session.commit(); audit(user.id,'login','user',user.id)
def logout_user():
    if g.get('current_user'): audit(g.current_user.id,'logout','user',g.current_user.id)
    session.clear()
def load_current_user():
    g.current_user=None; user_id=session.get('user_id')
    if not user_id: return
    user=db.session.get(User,user_id)
    if not user or not user.is_active or session.get('session_version')!=user.session_version or session.get('ua_hash')!=hash_user_agent(): session.clear(); return
    g.current_user=user
def set_password(user,password): user.set_password(password)
def create_password_reset_token(user,minutes=30):
    raw=secrets.token_urlsafe(32); h=hashlib.sha256(raw.encode()).hexdigest(); db.session.add(PasswordResetToken(user_id=user.id,token_hash=h,expires_at=utcnow()+timedelta(minutes=minutes))); db.session.commit(); return raw
def consume_password_reset_token(raw):
    h=hashlib.sha256(raw.encode()).hexdigest(); obj=db.session.execute(db.select(PasswordResetToken).where(PasswordResetToken.token_hash==h,PasswordResetToken.used_at.is_(None))).scalar_one_or_none()
    if not obj or obj.expires_at<utcnow(): return None
    obj.used_at=utcnow(); db.session.commit(); return obj.user
