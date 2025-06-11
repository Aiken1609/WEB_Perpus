from flask import Blueprint, render_template
from ..middleware.auth import get_current_user_info, redirect_by_role, token_required, admin_required
from backend.models import Buku

page_routes = Blueprint('page_routes', __name__)

@page_routes.route('/')
def home():
    return render_template('index.html')

@page_routes.route('/buku')
@token_required
def buku():
    return render_template('buku.html')

@page_routes.route('/dashboard')
@token_required
@admin_required
def dashboard():
    return render_template('dashboard.html')

@page_routes.route('/dbBuku')
@token_required
@admin_required
def dbBuku():
    return render_template('dbbuku.html')

@page_routes.route('/dbUser')
@token_required
@admin_required
def dbUser():
    return render_template('dbuser.html')

@page_routes.route('/dbReview')
@token_required
@admin_required
def dbReview():
    return render_template('dbreview.html')

@page_routes.route('/tambah')
@token_required
@admin_required
def tambah():
    return render_template('add_book.html')

@page_routes.route('/edit_book/<int:id_buku>', methods=['GET'])
@token_required
@admin_required
def edit_book(id_buku):
    book = Buku.query.get_or_404(id_buku)
    return render_template('edit_book.html', book=book)

@page_routes.route('/daftar', methods=['GET'])
def daftar():
    return render_template('daftar.html')

@page_routes.route('/login', methods=['GET'])
@redirect_by_role
def login():
    return render_template('login.html')