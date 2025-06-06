from datetime import datetime, timedelta
from models import db, Buku, User, Review, Rekomendasi
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

TOTAL_REKOMENDASI = 10

def hapus_rekomendasi_lama():
    batas_waktu = datetime.utcnow() - timedelta(days=1)
    Rekomendasi.query.filter(Rekomendasi.created_at < batas_waktu).delete()
    db.session.commit()

def dapatkan_review_user(id_user):
    return Review.query.filter_by(id_user=id_user).all()

def dapatkan_data_buku():
    buku_all = Buku.query.all()
    data = []
    for b in buku_all:
        data.append({
            'id_buku': b.id_buku,
            'genre': b.genre,
            'kategori': b.kategori,
            'rating': b.rating if b.rating is not None else 0.0
        })
    return pd.DataFrame(data)

def buat_rekomendasi(id_user):
    hapus_rekomendasi_lama()

    reviews = dapatkan_review_user(id_user)
    if len(reviews) < 1:
        # Jika kurang dari 1 review, rekomendasi fallback berdasar rating tertinggi buku
        top_buku = Buku.query.order_by(Buku.rating.desc()).limit(TOTAL_REKOMENDASI).all()

        # Hapus dulu rekomendasi lama user ini
        Rekomendasi.query.filter_by(id_user=id_user).delete()

        for buku in top_buku:
            rec = Rekomendasi(id_user=id_user, id_buku=buku.id_buku, created_at=datetime.utcnow())
            db.session.add(rec)
        db.session.commit()

        return [{"id_buku": b.id_buku, "msg": "Rekomendasi fallback rating tertinggi"} for b in top_buku]

    # Kalau ada review, lakukan rekomendasi berbasis model ML
    # Data review user
    df_reviews = pd.DataFrame([{
        'id_buku': r.id_buku,
        'genre': r.buku.genre,
        'kategori': r.buku.kategori,
        'rating': r.rating
    } for r in reviews])

    # Data semua buku
    df_buku = dapatkan_data_buku()

    # Gabungkan data review user dan data buku sebagai data latih (dummy buat contoh)
    # Untuk demo, kita asumsikan model sudah dilatih di sini (atau bisa load model eksternal)
    # Contoh RandomForest dummy training:

    # Encoding kategori dan genre ke angka (simple encoding)
    all_categories = list(set(df_buku['kategori'].unique()) | set(df_reviews['kategori'].unique()))
    all_genres = list(set(df_buku['genre'].unique()) | set(df_reviews['genre'].unique()))

    def encode_cat(val, all_vals):
        return all_vals.index(val) if val in all_vals else 0

    df_buku['kategori_enc'] = df_buku['kategori'].apply(lambda x: encode_cat(x, all_categories))
    df_buku['genre_enc'] = df_buku['genre'].apply(lambda x: encode_cat(x, all_genres))
    df_reviews['kategori_enc'] = df_reviews['kategori'].apply(lambda x: encode_cat(x, all_categories))
    df_reviews['genre_enc'] = df_reviews['genre'].apply(lambda x: encode_cat(x, all_genres))

    # Siapkan data latih dan target (rating sebagai label)
    X_train = df_reviews[['genre_enc', 'kategori_enc', 'rating']]
    y_train = (df_reviews['rating'] >= 3).astype(int)  # contoh label: 1 jika rating >=3 else 0

    # Latih model Random Forest
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Siapkan data untuk prediksi rekomendasi (buku yang belum di-review user)
    reviewed_ids = set(df_reviews['id_buku'])
    df_prediksi = df_buku[~df_buku['id_buku'].isin(reviewed_ids)].copy()

    if df_prediksi.empty:
        # Jika sudah review semua buku, fallback ke rekomendasi rating tertinggi
        top_buku = Buku.query.order_by(Buku.rating.desc()).limit(TOTAL_REKOMENDASI).all()
        Rekomendasi.query.filter_by(id_user=id_user).delete()
        for buku in top_buku:
            rec = Rekomendasi(id_user=id_user, id_buku=buku.id_buku, created_at=datetime.utcnow())
            db.session.add(rec)
        db.session.commit()
        return [{"id_buku": b.id_buku, "msg": "Rekomendasi fallback rating tertinggi"} for b in top_buku]

    # Encoding kolom prediksi
    df_prediksi['kategori_enc'] = df_prediksi['kategori'].apply(lambda x: encode_cat(x, all_categories))
    df_prediksi['genre_enc'] = df_prediksi['genre'].apply(lambda x: encode_cat(x, all_genres))

    # Prediksi probabilitas
    probs = model.predict_proba(df_prediksi[['genre_enc', 'kategori_enc', 'rating']])[:, 1]

    df_prediksi['prob'] = probs
    df_prediksi = df_prediksi.sort_values('prob', ascending=False)

    # Ambil top rekomendasi
    top_rekom = df_prediksi.head(TOTAL_REKOMENDASI)

    # Simpan ke DB, hapus dulu rekomendasi lama user ini
    Rekomendasi.query.filter_by(id_user=id_user).delete()

    hasil = []
    for _, row in top_rekom.iterrows():
        rec = Rekomendasi(id_user=id_user, id_buku=row['id_buku'], created_at=datetime.utcnow())
        db.session.add(rec)
        hasil.append({"id_buku": row['id_buku'], "prob": float(row['prob']), "msg": "Rekomendasi ML"})

    db.session.commit()
    return hasil
