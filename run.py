from flask import Flask
from flask_cors import CORS
from extentions import db, migrate, ma, jwt, mail
from app.routes import user_routes, recipe_routes
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, origins="*")
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(recipe_routes.bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
