from flask import Flask, request, jsonify, send_from_directory, session, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from functools import wraps
import os
import secrets
from sqlalchemy import func

from models import db, Buku, User, Review  # Import models dari models.py

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
        if 'username' not in session:
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
    user_id = session.get('id_user')
    user = User.query.get(user_id) if user_id else None
    return dict(user=user)

# ========== FRONTEND (TAMPILAN) ==========

@app.route('/syarat')
def index():
    return render_template('syarat.html')

@app.route('/buku')
@login_required
def buku():
    return render_template('buku.html')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/tambah')
@login_required
def tambah():
    return render_template('add_book.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/edit_book/<int:id_buku>', methods=['GET'])
@login_required
def edit_book(id_buku):
    book = Buku.query.get_or_404(id_buku)
    return render_template('edit_book.html', book=book)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = user.username
            session['role'] = user.role
            session['id_user'] = user.id_user

            if user.role == 'admin':
                return redirect(url_for('dashboard'))
            elif user.role == 'user':
                return redirect(url_for('buku'))
        else:
            return render_template('login.html', error="Username atau password salah!")

    return render_template('login.html')

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

from flask import session, jsonify, request

@app.route('/rating', methods=['POST'])
def submit_rating():
    if 'id_user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.form
    id_buku = data.get('buku_id')
    rating = int(data.get('rating'))
    id_user = session['id_user']

    existing_review = Review.query.filter_by(id_buku=id_buku, id_user=id_user).first()
    if existing_review:
        existing_review.rating = rating
    else:
        new_review = Review(id_buku=id_buku, id_user=id_user, rating=rating)
        db.session.add(new_review)

    db.session.commit()

    # Hitung ulang rating
    reviews = Review.query.filter_by(id_buku=id_buku).all()
    total_rating = sum([r.rating for r in reviews])
    jumlah_user = len(reviews)
    avg_rating = total_rating / jumlah_user if jumlah_user > 0 else 0

    buku = Buku.query.get(id_buku)
    buku.rating = round(avg_rating, 2)
    db.session.commit()

    return jsonify({
        "message": "Rating disimpan!",
        "average_rating": buku.rating,
        "jumlah_user": jumlah_user
    })

@app.route('/profile')
@login_required
def profile():
    id_user = session.get('id_user')

    user = User.query.filter_by(id_user=id_user).first()

    # Ambil semua review dari user ini
    user_reviews = Review.query.filter_by(id_user=id_user).all()

    # Ambil info buku dari tiap review
    reviewed_books = []
    for review in user_reviews:
        buku = Buku.query.get(review.id_buku)
        if buku:
            reviewed_books.append({
                'id_buku': buku.id_buku,
                'judul': buku.judul,
                'penerbit': buku.penerbit,
                'bahasa': buku.bahasa,
                'kategori': buku.kategori,
                'genre': buku.genre,
                'foto': buku.foto,
                'rating': review.rating
            })

    return render_template('profile.html', user=user, reviewed_books=reviewed_books)


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

@app.route('/add_book', methods=['POST'])
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

@app.route('/api/books', methods=['GET'])
def get_books():
    books = Buku.query.all()
    return jsonify([{ 
        'id_buku': b.id_buku,
        'judul': b.judul,
        'foto': b.foto,
        'penerbit': b.penerbit,
        'bahasa': b.bahasa,
        'kategori': b.kategori,
        'genre': b.genre,
        'deskripsi': b.deskripsi,
        'rating': b.rating
    } for b in books])

@app.route('/books/search', methods=['GET'])
def search_books():
    keyword = request.args.get('judul', '')
    books = Buku.query.filter(Buku.judul.ilike(f'%{keyword}%')).all()
    return jsonify([{ "id_buku": b.id_buku, "judul": b.judul } for b in books])

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
    return jsonify([{ "id_buku": b.id_buku, "judul": b.judul } for b in books])

@app.route('/edit_profile', methods=['PUT'])
@login_required
def edit_profile():
    user = User.query.get(session['id_user'])

    username = request.form.get('username')
    password = request.form.get('password')
    foto = request.files.get('foto')

    if username:
        user.username = username

    if password:
        user.password = password

    if foto:
        filename = secure_filename(foto.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(filepath)
        user.foto = filename

    db.session.commit()
    return jsonify({'message': 'Profil berhasil diperbarui'})


@app.route('/detail/<int:id_buku>', methods=['GET'])
@login_required
def detail(id_buku):
    buku = Buku.query.get_or_404(id_buku)

    total_rating = db.session.query(func.sum(Review.rating)).filter_by(id_buku=id_buku).scalar() or 0
    jumlah_user_rating = db.session.query(func.count(Review.id_user)).filter_by(id_buku=id_buku).scalar()
    average_rating = round(total_rating / jumlah_user_rating, 2) if jumlah_user_rating > 0 else 0

    id_user = session.get('id_user')
    user_review = Review.query.filter_by(id_buku=id_buku, id_user=id_user).first() if id_user else None

    return render_template('detail.html', 
        buku=buku,
        user_rating=user_review.rating if user_review else None,
        jumlah_user_rating=jumlah_user_rating,
        average_rating=average_rating
    )

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

if __name__ == '__main__':
    app.run(debug=True)
