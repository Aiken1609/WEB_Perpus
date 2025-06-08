# backend/AI/AI_route.py

from flask import Blueprint, g, request, jsonify
from datetime import datetime
from .AI_logic import predict_top_books
from backend.utils.fungsi_user import get_personal_reviews
from backend.models import Rekomendasi, db  # import model dan db
from backend.middleware.auth import token_required
ai_blueprint = Blueprint('ai_bp', __name__, url_prefix='/api/ai')


@ai_blueprint.route('/rekomendasi', methods=['POST'])
@token_required
def buat_rekomendasi_user():
    user_data = g.current_user
    user_id = user_data['id_user']
    if user_id is None:
        return jsonify({"status": "error", "message": "user_id tidak disediakan"}), 400

    # Ambil history review user
    personal_data = get_personal_reviews(user_id)
    user_reviews = personal_data.get("reviewed_books", [])

    # Dapatkan rekomendasi top-N
    recommendations = predict_top_books(user_reviews, top_n=9)
    print(f"Rekomendasi untuk user {user_id}: {recommendations}")
    # Simpan ke tabel rekomendasi
    now = datetime.utcnow()
    rec_objs = []
    for book in recommendations:
        rec = Rekomendasi(
            id_user=user_id,
            id_buku=book["id_buku"],
            created_at=now
        )
        rec_objs.append(rec)
        db.session.add(rec)

    # Commit semua sekaligus
    if rec_objs:
        db.session.commit()

    return jsonify({
        "status": "sukses",
        "user": personal_data.get("user"),
        "recommendations": recommendations
    })
