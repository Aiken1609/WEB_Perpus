from models import db
from models import Review, Buku  # pastikan Review dan Buku sudah ada di models.py
from sqlalchemy.orm import joinedload

def get_reviews_personal(user_id):
    """
    Mengambil data review personal user dari DB dan mengembalikannya
    dalam format dict sesuai yang dibutuhkan oleh fungsi rekomendasi_buku.
    Format:
    {
        "reviews": [
            {
                "rating": int,
                "buku": {
                    "id_buku": int,
                    "genre": str,
                    "kategori": str
                }
            },
            ...
        ]
    }
    """

    # Query data review user dengan join buku supaya bisa ambil genre & kategori
    reviews = db.session.query(Review).options(joinedload(Review.buku)).filter(Review.id_user == user_id).all()

    result = {"reviews": []}

    for rev in reviews:
        buku = rev.buku
        if buku:
            result["reviews"].append({
                "rating": rev.rating,
                "buku": {
                    "id_buku": buku.id_buku,
                    "genre": buku.genre,
                    "kategori": buku.kategori
                }
            })

    return result
