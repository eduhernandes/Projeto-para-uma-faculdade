from functools import wraps
from flask import abort, flash, g, redirect, url_for

def role_required(*roles):
    def deco(view):
        @wraps(view)
        def wrapped(*a,**kw):
            if not g.get('current_user'): flash('Faça login para continuar.','warning'); return redirect(url_for('auth.login'))
            if g.current_user.role not in roles: abort(403)
            return view(*a,**kw)
        return wrapped
    return deco

def permission_required(*perms):
    def deco(view):
        @wraps(view)
        def wrapped(*a,**kw):
            if not g.get('current_user'): flash('Faça login para continuar.','warning'); return redirect(url_for('auth.login'))
            if not all(g.current_user.has_permission(p) for p in perms): abort(403)
            return view(*a,**kw)
        return wrapped
    return deco
