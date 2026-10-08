from flask import Blueprint, render_template
from flask_wtf.csrf import CSRFError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
errors_bp=Blueprint('errors',__name__)

def render_error(code, message):
    template = f'errors/{code}.html' if code in {400,401,403,404,429,500} else 'errors/error.html'
    return render_template(template, code=code, message=message), code
@errors_bp.app_errorhandler(CSRFError)
def csrf_error(e): return render_error(400, 'A requisição não passou na verificação de segurança.')
@errors_bp.app_errorhandler(IntegrityError)
def integrity_error(e):
    from teofac.extensions import db
    db.session.rollback()
    return render_error(400, "Os dados enviados entram em conflito com um registro existente.")

@errors_bp.app_errorhandler(HTTPException)
def http_error(e):
    msg={400:'A requisição não pôde ser processada.',401:'Você precisa estar autenticado para acessar este recurso.',403:'Você não possui permissão para acessar este recurso.',404:'O recurso solicitado não foi encontrado.',429:'Muitas tentativas. Aguarde alguns minutos antes de tentar novamente.'}.get(e.code,'Não foi possível concluir a solicitação.')
    return render_error(e.code, msg)
@errors_bp.app_errorhandler(Exception)
def unhandled_error(e):
    from flask import current_app
    current_app.logger.exception('Erro interno não tratado')
    return render_error(500, 'Ocorreu um erro interno. Tente novamente.')
