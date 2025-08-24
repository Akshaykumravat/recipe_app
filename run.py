import os
import pytz
import logging
from flask import Flask
from flask_cors import CORS
from datetime import datetime
from app.routes.user_routes import create_admin
from logging.handlers import RotatingFileHandler
from extentions import db, migrate, ma, jwt, mail
from flask_swagger_ui import get_swaggerui_blueprint
from app.routes import (user_routes, 
                        recipe_routes, 
                        interactions_routes, 
                        role_routes, 
                        permission_routes)

def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, origins="*")

    app.cli.add_command(create_admin)

    # ✅ Setup Swagger UI
    SWAGGER_URL = '/api/docs'
    API_URL = r'\static\swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            'app_name': "Golden Recipe Application..!",
        },
    )

    app.register_blueprint(swaggerui_blueprint)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(recipe_routes.bp)
    app.register_blueprint(interactions_routes.bp)
    app.register_blueprint(role_routes.bp)
    app.register_blueprint(permission_routes.bp)

    
    setup_logging(app)

    return app


def setup_logging(app):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    file_handler = RotatingFileHandler("logs/app.log", maxBytes=10240, backupCount=5)
    file_handler.setLevel(logging.INFO)

    # ✅ Define IST Formatter
    class ISTFormatter(logging.Formatter):
        def converter(self, timestamp):
            dt = datetime.utcfromtimestamp(timestamp)
            ist = pytz.timezone("Asia/Kolkata")
            return dt.replace(tzinfo=pytz.utc).astimezone(ist)

        def formatTime(self, record, datefmt=None):
            dt = self.converter(record.created)
            if datefmt:
                return dt.strftime(datefmt)
            return dt.isoformat()

    formatter = ISTFormatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s',"%Y-%m-%d %I:%M:%S %p")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    # ✅ Also apply IST formatter to console (debug) output
    if app.debug:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(formatter)  # <-- KEY FIX
        app.logger.addHandler(stream_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Logging configured with IST timezone.")




app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
