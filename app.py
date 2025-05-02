from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from functools import wraps
import os
import secrets

from models import db, Buku, User  # Import models dari models.py

# --- Setup ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = secrets.token_hex(16)

# Buat folder uploads jika belum ada
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
 
# Inisialisasi database 
db.init_app(app)

# --- Middleware: login_required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization') or session.get('token')
        if not token or token != session.get('token'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- Buat database sebelum request pertama
@app.before_request
def create_tables():
    db.create_all()

# --- Routes Section ---

@app.context_processor
def inject_user():
    token = session.get('token')
    user = None
    if token:
        user = User.query.filter_by(role='user').first()
    return dict(user=user)

# ========== FRONTEND (TAMPILAN) ==========

@app.route('/syarat')
def index():
    return render_template('syarat.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/buku')
@login_required
def buku():
    return render_template('buku.html')

# Halaman Utama
@app.route('/')
def home():
    return render_template('index.html')



@app.route('/login', methods=['GET', 'POST'])
def loginle():
    return render_template('login.html')

def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['token'] = app.secret_key
            session['username'] = user.username
            session['role'] = user.role

            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            elif user.role == 'user':
                return redirect(url_for('buku'))
        else:
            return render_template('login.html', error="Username atau password salah!")

    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return render_template('daftar.html', error="Username sudah digunakan!")

        role = 'user'
        foto = request.files['foto']
        if foto:
            filename = secure_filename(foto.filename)
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            filename = 'default_profile.jpg'

        new_user = User(
            username=username,
            password=password,
            role=role,
            foto=filename,
        )
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('daftar.html')

# ========== BACKEND API (JSON) ==========

@app.route('/api/book/<int:id_buku>', methods=['GET'])
def get_book_detail(id_buku):
    book = Buku.query.get(id_buku)
    if book:
        return jsonify({
            'id_buku': book.id_buku,
            'judul': book.judul,
            'penerbit': book.penerbit,
            'bahasa': book.bahasa,
            'kategori': book.kategori,
            'genre': book.genre,
            'deskripsi': book.deskripsi,
            'foto': book.foto,
            'rating': book.rating
        })
    else:
        return jsonify({'error': 'Buku tidak ditemukan'}), 404

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({"filename": filename, "url": f"/uploads/{filename}"})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tambah')
@login_required
def tambah():
    return render_template('add_book.html')

@app.route('/add_book', methods=['POST'])
@login_required
def add_book():
    data = request.get_json()
    buku = Buku(
        judul=data['judul'],
        foto=data.get('foto', ''),
        penerbit=data.get('penerbit', ''),
        bahasa=data.get('bahasa', ''),
        kategori=data.get('kategori', ''),
        genre=data.get('genre', ''),
        deskripsi=data.get('deskripsi', ''),
        rating=data.get('rating', 0)
    )
    db.session.add(buku)
    db.session.commit()
    return jsonify({"message": "Buku berhasil ditambahkan!"}), 201

# API baru: Get Semua Buku dalam JSON
@app.route('/api/books', methods=['GET'])
def get_books():
    books = Buku.query.all()
    book_list = []
    for book in books:
        book_data = {
            'id_buku': book.id_buku,
            'judul': book.judul,
            'foto': book.foto,
            'penerbit': book.penerbit,
            'bahasa': book.bahasa,
            'kategori': book.kategori,
            'genre': book.genre,
            'deskripsi': book.deskripsi,
            'rating': book.rating
        }
        book_list.append(book_data)
    
    return jsonify(book_list)

@app.route('/books/search', methods=['GET'])
def search_books():
    keyword = request.args.get('judul', '')
    books = Buku.query.filter(Buku.judul.ilike(f'%{keyword}%')).all()
    return jsonify([{
        "id_buku": book.id_buku,
        "judul": book.judul
    } for book in books])

@app.route('/books/filter', methods=['GET'])
def filter_books():
    kategori = request.args.get('kategori')
    genre = request.args.get('genre')
    penerbit = request.args.get('penerbit')

    query = Buku.query
    if kategori:
        query = query.filter_by(kategori=kategori)
    if genre:
        query = query.filter_by(genre=genre)
    if penerbit:
        query = query.filter_by(penerbit=penerbit)

    books = query.all()
    return jsonify([{
        "id_buku": book.id_buku,
        "judul": book.judul
    } for book in books])

@app.route('/edit_book/<int:id_buku>', methods=['GET'])
@login_required
def edit_book(id_buku):
    book = Buku.query.get_or_404(id_buku)
    return render_template('edit_book.html', book=book)

@app.route('/update/<int:id_buku>', methods=['PUT'])
@login_required
def update_book(id_buku):
    data = request.get_json()
    book = Buku.query.get_or_404(id_buku)
    book.judul = data.get('judul', book.judul)
    book.foto = data.get('foto', book.foto)
    book.penerbit = data.get('penerbit', book.penerbit)
    book.bahasa = data.get('bahasa', book.bahasa)
    book.kategori = data.get('kategori', book.kategori)
    book.genre = data.get('genre', book.genre)
    book.deskripsi = data.get('deskripsi', book.deskripsi)
    db.session.commit()
    return jsonify({"message": "Buku berhasil diupdate!"})


@app.route('/delete_book/<int:id_buku>', methods=['DELETE'])
@login_required
def delete_book(id_buku):
    book = Buku.query.get_or_404(id_buku)
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Buku berhasil dihapus!"})

# --- Run App ---
if __name__ == '__main__':
    app.run(debug=True)
