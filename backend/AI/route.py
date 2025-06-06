from flask import Blueprint, jsonify, request, g
from flask_login import login_required
from models import Rekomendasi
from backend.AI.logic import buat_rekomendasi  # pastikan ini sudah ada

ai_blueprint = Blueprint('ai_blueprint', __name__)

@ai_blueprint.route('/api/rekomendasi', methods=['GET'])
@login_required
def api_rekomendasi():
    user_id = g.current_user
    rekomendasi = Rekomendasi.query.filter_by(id_user=user_id).all()
    data = []
    for r in rekomendasi:
        data.append({
            "id_buku": r.id_buku,
            "foto": r.foto,
            "judul": r.judul,
            "penerbit": r.penerbit,
            "bahasa": r.bahasa,
            "kategori": r.kategori,
            "genre": r.genre,
            "rating": r.rating,
        })
    return jsonify(data)

@ai_blueprint.route('/api/rekomendasi_ai', methods=['GET'])
@login_required
def rekomendasi_ai():
    user_id = g.current_user
    try:
        rekomendasi_result = buat_rekomendasi(user_id)
        return jsonify(rekomendasi_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
