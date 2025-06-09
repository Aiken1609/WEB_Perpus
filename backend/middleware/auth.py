# middleware/auth.py
from functools import wraps
from flask import request, jsonify, redirect, url_for, g
from flask import current_app as app
import jwt
from backend.models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        # print("Token dari cookie:", token)  # debug print
        if not token:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'message': 'Token tidak ditemukan'}), 401
            else:
                return redirect(url_for('page_routes.login'))

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = data
        except jwt.ExpiredSignatureError:
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'message': 'Token kadaluarsa'}), 401
            else:
                return redirect(url_for('page_routes.login'))
        except jwt.InvalidTokenError:
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'message': 'Token tidak valid'}), 401
            else:
                return redirect(url_for('page_routes.login'))

        return f(*args, **kwargs)
    return decorated

def get_current_user_info():
    user_data = g.current_user
    id_user = user_data['id_user']
    user = User.query.filter_by(id_user=id_user).first()
    if not user:
        return jsonify({'message': 'User tidak ditemukan'}), 404
    return jsonify({
        'id_user': user.id_user,
        'username': user.username,
        'role': user.role,
        'foto': user.foto
    })

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_data = g.current_user
        id_user = user_data.get('id_user')
        user = User.query.filter_by(id_user=id_user).first()
        if not user or user.role != 'admin':
            if 'application/json' in request.headers.get('Accept', ''):
                return jsonify({'message': 'Anda bukan admin'}), 403
            else:
                return redirect(url_for('page_routes.login', message='anda bukan admin'))
        return f(*args, **kwargs)
    return decorated