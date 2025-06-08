from flask import Blueprint, render_template, request, jsonify, g, current_app
from ..middleware.auth import token_required, admin_required
from backend.models import db, Buku, User, Review, Rekomendasi
from ..utils.fungsi_user import get_personal_reviews
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
from backend.AI.AI_route import buat_rekomendasi_user

api_routes = Blueprint('api_routes', __name__)

@api_routes.route('/profile')
@token_required
def profile():
    user_data = g.current_user
    id_user = user_data['id_user']
    user = User.query.get(id_user)

    data = get_personal_reviews(id_user)
    reviewed_books = data['reviewed_books']
    user_review_info = data['user']  

    return render_template(
        'profile.html',
        user=user,
        reviewed_books=reviewed_books,
        user_review_info=user_review_info
    )

@api_routes.route('/api/readRekomendasi', methods=['GET'])
@token_required
def get_rekomendasi_user():
    id_user = g.current_user['id_user']

    # Hapus rekomendasi lama user ini
    db.session.query(Rekomendasi).filter_by(id_user=id_user).delete()
    db.session.commit()

    # Buat rekomendasi baru (menggunakan g.current_user di dalam fungsinya)
    buat_rekomendasi_user()

    # Ambil hasil rekomendasi terbaru dari DB
    rekom = db.session.query(Rekomendasi, Buku).join(Buku, Rekomendasi.id_buku == Buku.id_buku)\
        .filter(Rekomendasi.id_user == id_user).all()

    hasil = [{
        'id_buku': b.id_buku,
        'judul': b.judul,
        'foto': b.foto,
        'genre': b.genre,
        'kategori': b.kategori,
        'rating': b.rating
    } for _, b in rekom]

    return jsonify({
        "status": "sukses",
        "jumlah": len(hasil),
        "rekomendasi": hasil
    })

@api_routes.route('/api/reviews_personal', methods=['GET'])
@token_required
def api_personal_reviews():
    id_user = g.current_user['id_user']
    data = get_personal_reviews(id_user)
    return jsonify(data)

@api_routes.route('/api/reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.all()
    result = []
    for r in reviews:
        result.append({
            'id_review': r.id_review,
            'id_buku': r.id_buku,
            'id_user': r.id_user,
            'rating': r.rating,
            'created_at': r.created_at
        })
    return jsonify(result)

@api_routes.route('/api/reviews_full', methods=['GET'])
@token_required
def get_reviews_full():
    reviews = db.session.query(
        Review.id_review,
        Review.rating,
        Review.created_at,
        Buku.id_buku,
        Buku.judul,
        Buku.foto.label('foto_buku'),
        Buku.penerbit,
        Buku.bahasa,
        Buku.kategori,
        Buku.genre,
        User.id_user,
        User.username,
        User.foto.label('foto_user'),
        User.role
    ).join(Buku, Review.id_buku == Buku.id_buku)\
        .join(User, Review.id_user == User.id_user).all()

    result = []
    for r in reviews:
        result.append({
            'id_review': r.id_review,
            'rating': r.rating,
            'created_at': r.created_at,
            'buku': {
                'id_buku': r.id_buku,
                'judul': r.judul,
                'foto': r.foto_buku,
                'penerbit': r.penerbit,
                'bahasa': r.bahasa,
                'kategori': r.kategori,
                'genre': r.genre
            },
            'user': {
                'id_user': r.id_user,
                'username': r.username,
                'foto': r.foto_user,
                'role': r.role
            }
        })
    return jsonify(result)

@api_routes.route('/rating', methods=['POST'])
@token_required
def submit_rating():
    user_data = g.current_user
    id_user = user_data['id_user']
    data = request.form
    id_buku = data.get('buku_id')
    rating = int(data.get('rating'))

    existing_review = Review.query.filter_by(id_buku=id_buku, id_user=id_user).first()
    if existing_review:
        existing_review.rating = rating
    else:
        new_review = Review(id_buku=id_buku, id_user=id_user, rating=rating)
        db.session.add(new_review)

    db.session.commit()

    reviews = Review.query.filter_by(id_buku=id_buku).all()
    avg_rating = sum([r.rating for r in reviews]) / len(reviews) if reviews else 0
    buku = Buku.query.get(id_buku)
    buku.rating = round(avg_rating, 2)
    db.session.commit()

    return jsonify({"message": "Rating disimpan!", "average_rating": buku.rating, "jumlah_user": len(reviews)})

@api_routes.route('/api/books', methods=['GET'])
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

@api_routes.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{
        'id_user': u.id_user,
        'username': u.username,
        'role': u.role,
        'foto': u.foto
    } for u in users])

@api_routes.route('/api/user/<int:id_user>', methods=['GET'])
def get_user_by_id(id_user):
    user = User.query.get(id_user)
    if user:
        return jsonify({
            'id_user': user.id_user,
            'username': user.username,
            'role': user.role,
            'foto': user.foto
        })
    else:
        return jsonify({'message': 'User tidak ditemukan'}), 404
    
@api_routes.route('/api/book/<int:id_buku>', methods=['GET'])
@token_required
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

@api_routes.route('/api/search_review', methods=['GET'])
@token_required
def search_review():
    query = request.args.get('q', '')
    username = request.args.get('username', '')

    q_review = db.session.query(
        Review.id_review,
        Review.rating,
        Review.created_at,
        Buku.judul,
        Buku.foto.label('foto_buku'),
        User.username,
        User.foto.label('foto_user')
    ).join(Buku, Review.id_buku == Buku.id_buku)\
        .join(User, Review.id_user == User.id_user)

    if query:
        q_review = q_review.filter(Buku.judul.ilike(f"%{query}%"))
    if username:
        q_review = q_review.filter(User.username.ilike(f"%{username}%"))

    results = []
    for r in q_review.all():
        results.append({
            'review': {
                'id_review': r.id_review,
                'rating': r.rating,
                'created_at': r.created_at
            },
            'buku': {
                'judul': r.judul,
                'foto': r.foto_buku
            },
            'user': {
                'username': r.username,
                'foto': r.foto_user
            }
        })
    return jsonify(results)

@api_routes.route('/api/search', methods=['GET'])
@token_required
def search_books():
    query = request.args.get('q', '')
    genre = request.args.get('genre', '')
    kategori = request.args.get('kategori', '')
    penerbit = request.args.get('penerbit', '')

    filters = []
    if query:
        filters.append(Buku.judul.ilike(f"%{query}%"))
    if genre:
        filters.append(Buku.genre.ilike(f"%{genre}%"))
    if kategori:
        filters.append(Buku.kategori.ilike(f"%{kategori}%"))
    if penerbit:
        filters.append(Buku.penerbit.ilike(f"%{penerbit}%"))

    if filters:
        books = Buku.query.filter(*filters).all()
    else:
        books = Buku.query.all()

    result = [{
        'id_buku': b.id_buku,
        'judul': b.judul,
        'penerbit': b.penerbit,
        'bahasa': b.bahasa,
        'kategori': b.kategori,
        'genre': b.genre,
        'deskripsi': b.deskripsi,
        'foto': b.foto,
        'rating': b.rating
    } for b in books]

    return jsonify(result)

@api_routes.route('/api/search_user', methods=['GET'])
@token_required
def search_users():
    query = request.args.get('q', '')
    role = request.args.get('role', '')

    filters = []
    if query:
        filters.append(User.username.ilike(f"%{query}%"))
    if role:
        filters.append(User.role.ilike(f"%{role}%"))

    if filters:
        users = User.query.filter(*filters).all()
    else:
        users = User.query.all()

    result = [{
        'id_user': u.id_user,
        'username': u.username,
        'role': u.role,
        'foto': u.foto
    } for u in users]

    return jsonify(result)


##################################################################################################################
# CRUD Admin & User
##################################################################################################################


#USER CRUD

@api_routes.route('/detail/<int:id_buku>', methods=['GET'])
@token_required
def detail_buku(id_buku):
    # Ambil data buku menggunakan fungsi get_book_detail
    response = get_book_detail(id_buku)
    if response.status_code == 404:
        return render_template('404.html'), 404

    # response bisa berupa tuple (json, status_code) atau Response object
    if isinstance(response, tuple):
        book_data = response[0].get_json()
    else:
        book_data = response.get_json()
    return render_template('detail.html', buku=book_data)

@api_routes.route('/edit_profile', methods=['PUT'])
@token_required
def edit_profile():
    user_data = g.current_user
    user = User.query.get(user_data['id_user'])
    username = request.form.get('username')
    password = request.form.get('password')
    foto = request.files.get('foto')

    # Cek apakah username sudah digunakan oleh user lain
    if username and username != user.username:
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({'error': 'Username sudah digunakan!'}), 400
        user.username = username

    if password:
        user.password = generate_password_hash(password)
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        foto.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        user.foto = filename

    db.session.commit()
    return jsonify({'message': 'Profil berhasil diperbarui'})

@api_routes.route('/delete_review/<int:id_buku>', methods=['DELETE'])
@token_required
def delete_review(id_buku):
    user_data = g.current_user
    id_user = user_data['id_user']
    
    review = Review.query.filter_by(id_buku=id_buku, id_user=id_user).first()
    if not review:
        return jsonify({'message': 'Review tidak ditemukan'}), 404

    db.session.delete(review)
    
    # Update rating buku
    reviews = Review.query.filter_by(id_buku=id_buku).all()
    avg_rating = sum([r.rating for r in reviews]) / len(reviews) if reviews else 0
    buku = Buku.query.get(id_buku)
    if buku:
        buku.rating = round(avg_rating, 2)
        
    db.session.commit()
    return jsonify({'message': 'Review berhasil dihapus'})


#ADMIN CRUD

@api_routes.route('/add_book', methods=['POST'])
@token_required
@admin_required
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

@api_routes.route('/add_books', methods=['POST'])
@token_required
@admin_required
def add_books():
    data = request.get_json()
    
    # Check if data is a list (bulk insert) or single dictionary
    if isinstance(data, list):
        books = []
        for book_data in data:
            buku = Buku(
                judul=book_data['judul'],
                foto=book_data.get('foto', ''),
                penerbit=book_data.get('penerbit', ''),
                bahasa=book_data.get('bahasa', ''),
                kategori=book_data.get('kategori', ''),
                genre=book_data.get('genre', ''),
                deskripsi=book_data.get('deskripsi', ''),
                rating=book_data.get('rating', 0)
            )
            books.append(buku)
        
        db.session.bulk_save_objects(books)
        db.session.commit()
        return jsonify({"message": f"{len(books)} buku berhasil ditambahkan!"}), 201
    else:
        # Handle single book addition
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

@api_routes.route('/update/<int:id_buku>', methods=['PUT'])
@token_required
@admin_required
def update_book(id_buku):
    data = request.get_json()
    book = Buku.query.get_or_404(id_buku)
    book.judul = data.get('judul', book.judul)
    foto_baru = data.get('foto')
    if not foto_baru:
        # Ambil data buku dari database untuk mendapatkan foto lama
        buku_lama = Buku.query.get(id_buku)
        book.foto = buku_lama.foto
    else:
        book.foto = foto_baru
    book.penerbit = data.get('penerbit', book.penerbit)
    book.bahasa = data.get('bahasa', book.bahasa)
    book.kategori = data.get('kategori', book.kategori)
    book.genre = data.get('genre', book.genre)
    book.deskripsi = data.get('deskripsi', book.deskripsi)
    db.session.commit()
    return jsonify({"message": "Buku berhasil diupdate!"})

@api_routes.route('/delete_book/<int:id_buku>', methods=['DELETE'])
@token_required
@admin_required
def delete_book(id_buku):
    book = Buku.query.get_or_404(id_buku)
    user_reviews = Review.query.filter_by(id_buku=id_buku).all()
    buku_ids = list(set([review.id_buku for review in user_reviews]))

    # Hapus semua review milik user ini
    Review.query.filter_by(id_buku=id_buku).delete()

    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Buku berhasil dihapus!"})