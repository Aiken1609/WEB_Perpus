from models import Review, Buku, User, db
from sqlalchemy import func

def get_personal_reviews(id_user):
    reviews = db.session.query(
        Review.id_review,
        Review.rating.label('rating_review'),
        Review.created_at,
        Buku.id_buku,
        Buku.judul,
        Buku.foto.label('foto_buku'),
        Buku.penerbit,
        Buku.bahasa,
        Buku.kategori,
        Buku.genre,
        Buku.rating.label('rating_buku'),
        User.id_user,
        User.username,
        User.foto.label('foto_user'),
        User.role
    ).join(Buku, Review.id_buku == Buku.id_buku)\
     .join(User, Review.id_user == User.id_user)\
     .filter(Review.id_user == id_user).all()

    review_list = []
    user_info = None

    for r in reviews:
        if user_info is None:
            user_info = {
                'id_user': r.id_user,
                'username': r.username,
                'foto': r.foto_user,
                'role': r.role
            }
        review_list.append({
            'id_review': r.id_review,
            'rating': r.rating_review,
            'created_at': r.created_at,
            'buku': {
                'id_buku': r.id_buku,
                'judul': r.judul,
                'foto': r.foto_buku,
                'penerbit': r.penerbit,
                'bahasa': r.bahasa,
                'kategori': r.kategori,
                'genre': r.genre,
                'rating': r.rating_buku
            }
        })

    return {
        'user': user_info,
        'reviews': review_list
    }