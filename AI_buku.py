import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from app import api_personal_reviews

GENRE_LIST = ["Pengetahuan Umum", "Sci-fi", "Petualangan", "Sejarah", "Horror"]
KATEGORI_LIST = ["Ensiklopedia", "Komik", "Novel"]

def map_genre(genre):
    return genre if genre in GENRE_LIST else "Pengetahuan Umum"

def map_kategori(kategori):
    return kategori if kategori in KATEGORI_LIST else "Lainnya"

def fetch_reviews_personal():
    """
    Ambil data review user saat ini langsung dari fungsi di app.py
    """
    try:
        return api_personal_reviews()
    except Exception as e:
        print("Error saat ambil data:", e)
        return []

def train_model():
    reviews = fetch_reviews_personal()
    if not reviews:
        return None, pd.DataFrame()

    data = {
        'id_buku': [],
        'genre': [],
        'kategori': [],
        'rating': [],
        'direkomendasikan': []
    }

    for r in reviews:
        buku = r['buku']
        data['id_buku'].append(buku.get('id_buku'))
        data['genre'].append(map_genre(buku.get('genre', 'Pengetahuan Umum')))
        data['kategori'].append(map_kategori(buku.get('kategori', 'Lainnya')))
        data['rating'].append(r['rating'])
        data['direkomendasikan'].append(1 if r['rating'] >= 4 else 0)

    df = pd.DataFrame(data)
    df['genre'] = pd.Categorical(df['genre'], categories=GENRE_LIST).codes
    df['kategori'] = pd.Categorical(df['kategori'], categories=KATEGORI_LIST + ["Lainnya"]).codes

    X = df[['genre', 'kategori', 'rating']]
    y = df['direkomendasikan']

    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    return model, df

def rekomendasi_buku(input_buku, top_n=3, total_rekomendasi=6):
    model, df = train_model()
    if model is None or df.empty:
        return []

    input_df = pd.DataFrame(input_buku)
    input_df['genre'] = pd.Categorical(
        input_df['genre'].apply(map_genre), categories=GENRE_LIST
    ).codes
    input_df['kategori'] = pd.Categorical(
        input_df['kategori'].apply(map_kategori), categories=KATEGORI_LIST + ["Lainnya"]
    ).codes
    probs = model.predict_proba(input_df)[:, 1]
    input_df['prob_rekomendasi'] = probs
    rekomendasi = input_df.sort_values('prob_rekomendasi', ascending=False).head(top_n)

    hasil = []
    rekomendasi_ids = set()

    for _, row in rekomendasi.iterrows():
        mask_both = (df['genre'] == row['genre']) & (df['kategori'] == row['kategori'])
        mask_genre = (df['genre'] == row['genre'])
        mask_kategori = (df['kategori'] == row['kategori'])

        kandidat = None
        msg = ""
        if df[mask_both].shape[0] > 0:
            kandidat = df[mask_both].iloc[(df[mask_both]['rating'] - row['rating']).abs().argsort()]
            msg = "Rekomendasi buku yang serupa"
        elif df[mask_genre].shape[0] > 0:
            kandidat = df[mask_genre].iloc[(df[mask_genre]['rating'] - row['rating']).abs().argsort()]
            msg = "Rekomendasi genre yang serupa"
        elif df[mask_kategori].shape[0] > 0:
            kandidat = df[mask_kategori].iloc[(df[mask_kategori]['rating'] - row['rating']).abs().argsort()]
            msg = "Rekomendasi kategori yang serupa"
        else:
            kandidat = df.sort_values('rating', ascending=False)
            msg = "Rekomendasi dengan rating tertinggi"

        count = 0
        for _, k in kandidat.iterrows():
            if k['id_buku'] not in rekomendasi_ids:
                hasil.append({
                    "id_buku": k['id_buku'],
                    "msg": msg
                })
                rekomendasi_ids.add(k['id_buku'])
                count += 1
                if count >= 3:
                    break

        if len(hasil) >= total_rekomendasi:
            break

    if len(hasil) < total_rekomendasi:
        tambahan = df[~df['id_buku'].isin(rekomendasi_ids)].sort_values('rating', ascending=False)
        for _, k in tambahan.iterrows():
            hasil.append({
                "id_buku": k['id_buku'],
                "msg": "Rekomendasi tambahan rating tertinggi"
            })
            if len(hasil) >= total_rekomendasi:
                break

    return hasil[:total_rekomendasi]

# # Contoh penggunaan
# if __name__ == "__main__":
#     buku_baru = [
#         {'genre': 'Sci-fi', 'kategori': 'Novel', 'rating': 4.3},
#         {'genre': 'Sejarah', 'kategori': 'Ensiklopedia', 'rating': 4.1},
#         {'genre': 'Horror', 'kategori': 'Komik', 'rating': 3.8}
#     ]
#     hasil = rekomendasi_buku(buku_baru, total_rekomendasi=6)
#     print(hasil)
