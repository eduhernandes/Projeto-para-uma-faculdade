from flask import Blueprint,flash,redirect,render_template,url_for
from ..extensions import limiter
from ..forms import LoginForm
from ..services.auth import authenticate,login_user,logout_user
from ..decorators import role_required

auth_bp=Blueprint('auth',__name__,url_prefix='/auth')
@auth_bp.route('/login',methods=['GET','POST'])
@limiter.limit('5 per 15 minutes',methods=['POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=authenticate(form.identifier.data,form.password.data)
        if user:
            login_user(user); flash('Login realizado com sucesso.','success'); return redirect(url_for('main.dashboard'))
        flash('Usuário/e-mail ou senha inválidos.','danger')
    return render_template('auth/login.html',form=form)
@auth_bp.post('/logout')
def logout():
    from flask import g
    if not g.get('current_user'): return redirect(url_for('auth.login'))
    logout_user(); flash('Sessão encerrada.','info'); return redirect(url_for('auth.login'))
@auth_bp.get('/recuperar-senha')
def password_recovery(): return render_template('auth/recovery.html')
