import json
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

# 1. Load data JSON
with open("backend/AI/model/sample_review_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 2. Parse review ke DataFrame
rows = []
for item in data["reviewed_books"]:
    buku = item["review"]["buku"]
    rows.append({
        "id_buku": buku["id_buku"],           # ID hanya untuk referensi
        "bahasa": buku["bahasa"],
        "kategori": buku["kategori"],
        "genre": buku["genre"],
        "rating_buku": buku["rating"],
        "rating_user": item["review"]["rating"]
    })
df = pd.DataFrame(rows)

print("Data parsed ke DataFrame:")
print(df.head())

# 3. Validasi jumlah data per kelas rating
rating_counts = df["rating_user"].value_counts()
print("\nJumlah data per kelas rating:")
print(rating_counts)

# 4. Siapkan fitur (X) dan label (y)
X = df.drop(columns=["id_buku", "rating_user"])
y = df["rating_user"]

# 5. Preprocessing pipeline: OneHotEncoder untuk fitur kategorikal
categorical_cols = ["bahasa", "kategori", "genre"]
numeric_cols = ["rating_buku"]

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols)
    ],
    remainder="passthrough"  # kolom numerik tetap
)


# 6. Gabungkan preprocessing, SMOTE, dan model ke dalam pipeline

smote = SMOTE(random_state=42, k_neighbors=1)
model = ImbPipeline(steps=[
    ("preprocessor", preprocessor),
    ("smote", smote),                  # tambah SMOTE di pipeline
    ("classifier", RandomForestClassifier(random_state=42))
])
# 7. Grid search untuk tuning hyperparameter
param_grid = {
    "classifier__n_estimators": [100, 200],
    "classifier__max_depth": [None, 10, 20],
    "classifier__min_samples_split": [2, 5],
    "classifier__min_samples_leaf": [1, 2]
}

grid_search = GridSearchCV(
    model,
    param_grid=param_grid,
    cv=3,
    scoring="accuracy",
    verbose=1,
    n_jobs=-1
)

# 8. Train-test split dan fit
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_
print("✅ Parameter terbaik:", grid_search.best_params_)

# 9. Evaluasi
y_pred = best_model.predict(X_test)
print("\n📊 Classification Report:")
print(classification_report(y_test, y_pred, zero_division=0))

# 10. Simpan model pipeline (termasuk encoder dan SMOTE)
with open("backend/AI/rf_model.pkl", "wb") as f:
    pickle.dump(best_model, f)

print("✅ Model pipeline berhasil disimpan.")
