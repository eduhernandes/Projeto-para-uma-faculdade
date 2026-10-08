from flask import Blueprint,g,redirect,render_template,url_for
from ..decorators import role_required
main_bp=Blueprint('main',__name__)
@main_bp.get('/')
def index(): return redirect(url_for('main.dashboard')) if g.get('current_user') else render_template('landing.html')
@main_bp.get('/dashboard')
def dashboard():
    if not g.get('current_user'): return redirect(url_for('auth.login'))
    return redirect({'admin': 'admin.dashboard','teacher':'teacher.dashboard','student':'student.dashboard'}[g.current_user.role])
