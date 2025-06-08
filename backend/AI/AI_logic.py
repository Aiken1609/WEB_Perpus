import pickle
import pandas as pd
from ..models import Buku  # SQLAlchemy model Buku

# Load pipeline model (sudah termasuk preprocessing)
with open("backend/AI/rf_model.pkl", "rb") as f:
    model = pickle.load(f)

def predict_top_books(user_reviews: list, top_n: int = 9) -> list:
    """
    user_reviews: list of review dicts (struktur sample_review_data.json)
    top_n: jumlah rekomendasi yang diinginkan
    """
    # 1. Filter review positif dan ambil preferensi
    positive = [
        r["review"]["buku"]
        for r in user_reviews
        if r["review"]["rating"] > 3
    ]
    if not positive:
        return []

    pref_df = pd.DataFrame(positive)
    preferensi = {}
    for col in ["kategori", "genre", "bahasa"]:
        if col in pref_df.columns:
            preferensi[col] = pref_df[col].mode()[0]

    # 2. Ambil semua buku dari database
    all_books = Buku.query.all()
    reviewed_ids = {r["review"]["buku"]["id_buku"] for r in user_reviews}

    # 3. Filter buku yang belum direview & cocok preferensi
    candidates = []
    for b in all_books:
        if b.id_buku in reviewed_ids:
            continue
        # minimal satu preferensi cocok
        if any(getattr(b, k) == v for k, v in preferensi.items()):
            candidates.append(b)

    if not candidates:
        return []

    # 4. Buat DataFrame kandidat
    df_cand = pd.DataFrame([{
        "id_buku": b.id_buku,
        "judul": b.judul,
        "foto": b.foto,
        "deskripsi": b.deskripsi,
        "bahasa": b.bahasa,
        "penerbit": b.penerbit,
        "kategori": b.kategori,
        "genre": b.genre,
        "rating_buku": b.rating
    } for b in candidates])

    # 5. Prediksi rating menggunakan pipeline model
    feature_cols = ["bahasa", "kategori", "genre", "rating_buku"]
    df_feat = df_cand[feature_cols]

    df_cand["predicted_rating"] = model.predict(df_feat)
    df_cand["distance_to_5"] = (5 - df_cand["predicted_rating"]).abs()

    # 6. Pilih top-N berdasarkan prediksi terdekat ke 5
    top_df = df_cand.nsmallest(top_n, "distance_to_5")

    return top_df.drop(columns=["distance_to_5"]).to_dict(orient="records")
