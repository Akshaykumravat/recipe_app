from flask import Flask
from flask_cors import CORS
from extentions import db, migrate, ma, jwt, mail
from app.routes import user_routes, recipe_routes, interactions_routes
from flask_swagger_ui import get_swaggerui_blueprint


def create_app():
    app = Flask(__name__, template_folder='templates')
    app.config.from_object("config.Config")

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, origins="*")

    SWAGGER_URL = '/api/docs'  
    API_URL = r'\static\swagger.json'
    swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL,
        config={  
            'app_name': "Golden Recipe Application..!",
        },
    )

    app.register_blueprint(swaggerui_blueprint)
    app.register_blueprint(user_routes.bp)
    app.register_blueprint(recipe_routes.bp)
    app.register_blueprint(interactions_routes.bp)



    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
