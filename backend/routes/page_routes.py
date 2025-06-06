from flask import Blueprint, g, render_template, current_app, send_from_directory
from ..middleware.auth import token_required, admin_required
from models import Buku, User
from ..utils.fungsi_user import get_personal_reviews

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

@page_routes.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

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

@page_routes.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@page_routes.route('/profile')
@token_required
def profile():
    user_data = g.current_user
    id_user = user_data['id_user']
    user = User.query.get(id_user)

    data = get_personal_reviews(id_user)
    reviewed_books = data['reviews']
    user_review_info = data['user']  

    return render_template(
        'profile.html',
        user=user,
        reviewed_books=reviewed_books,
        user_review_info=user_review_info
    )
