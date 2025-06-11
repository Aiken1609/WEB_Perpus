from flask import Blueprint, g, request, jsonify, make_response, redirect, url_for, render_template
from werkzeug.security import check_password_hash, generate_password_hash
import jwt, datetime
from flask import current_app as app
from ..middleware.auth import token_required, get_current_user_info
from backend.models import db, Buku, User, Review

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username dan password wajib diisi!'}), 400
    user = User.query.filter_by(username=data.get('username')).first()
    if not user:
        return jsonify({'message': 'Akun belum terdaftar!'}), 404

    if not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Username atau password salah!'}), 401

    token = jwt.encode({
        'id_user': user.id_user,
        'username': user.username,
        'role': user.role,
        'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=2)
    }, app.config['SECRET_KEY'], algorithm='HS256')
    print("Token dari cookie:", token)
    response = make_response(jsonify({
        'message': 'Login berhasil',
        'user': {
            'id_user': user.id_user,
            'username': user.username,
            'role': user.role,
            'foto': user.foto
        }
    }))
    response.set_cookie('token', token, httponly=True, samesite='Lax')
    return response

@auth_routes.route('/check_token')
@token_required
def check_token():
    token = request.cookies.get('token')
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    return jsonify({'token': token})
    
@auth_routes.route('/api/daftar', methods=['POST'])
def api_daftar():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username dan password wajib diisi!'}), 400

    username = data['username']
    password = data['password']

    # Cek apakah username sudah digunakan
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username sudah digunakan!'}), 409

    hashed_password = generate_password_hash(password)
    foto = data.get('foto')
    # foto sekarang berupa URL string, jika kosong pakai default
    foto_url = foto if foto else '/static/default_profile.jpg'

    new_user = User(
        username=username,
        password=hashed_password,
        role='user',
        foto=foto_url
    )

    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registrasi berhasil!'}), 201

@auth_routes.route('/thisuser', methods=['GET'])
@token_required
def current_user():
    return get_current_user_info()

@auth_routes.route('/logout')
@token_required
def logout():
    resp = make_response(redirect(url_for('page_routes.login')))
    resp.delete_cookie('token')
    return resp

@auth_routes.route('/delete_user', methods=['DELETE'])
@token_required
def delete_user():
    user_data = g.current_user
    id_user = user_data['id_user']
    user = User.query.filter_by(id_user=id_user).first()
    if not user:
        return jsonify({'message': 'User tidak ditemukan'}), 404

    # Ambil semua review milik user ini sebelum dihapus
    user_reviews = Review.query.filter_by(id_user=id_user).all()
    buku_ids = list(set([review.id_buku for review in user_reviews]))

    # Hapus semua review milik user ini
    Review.query.filter_by(id_user=id_user).delete()

    # Hapus user
    db.session.delete(user)
    db.session.commit()

    # Kalkulasi ulang rating untuk setiap buku yang direview user ini
    for id_buku in buku_ids:
        reviews = Review.query.filter_by(id_buku=id_buku).all()
        avg_rating = sum([r.rating for r in reviews]) / len(reviews) if reviews else 0
        buku = Buku.query.get(id_buku)
        if buku:
            buku.rating = round(avg_rating, 2)
    db.session.commit()
    resp = make_response(jsonify({'message': 'Akun dan review berhasil dihapus'}))
    resp.delete_cookie('token')
    return resp
