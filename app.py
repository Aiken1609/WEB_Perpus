from flask import Flask
import os
from backend.models import db
from backend.routes.page_routes import page_routes
from backend.routes.api_routes import api_routes
from backend.routes.auth_routes import auth_routes
from backend.AI.AI_route import ai_blueprint
from supabase import create_client
# from backend.routes.api_routes import api_personal_reviews
# from backend.AI.logic import set_api_personal_reviews
from dotenv import load_dotenv
app = Flask(__name__)
load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')
JWT_SECRET = app.config['SECRET_KEY']
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db.init_app(app)
app.register_blueprint(page_routes)
app.register_blueprint(api_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(ai_blueprint) # Register AI routes

# set_api_personal_reviews(api_personal_reviews)

@app.before_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


