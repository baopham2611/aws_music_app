# application.__init__.py
"""Initialize app."""

from flask import Flask, jsonify, request, session
from flask_login import login_user, LoginManager
from flask_bootstrap import Bootstrap
from flask_marshmallow import Marshmallow
from .model.sessions import Session
from config import DevelopmentConfig, ProductionConfig, TestingConfig
import os
 
ma = Marshmallow()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from flask import session
    from .model.sessions import Session
    return Session( name=session.get('name'), email=session.get('email'))

def create_app():
    """
        Construct the core app object.
        Define the WSGI application object
    """
    app = Flask(__name__, instance_relative_config=False)


    env_config = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }.get(os.getenv('FLASK_ENV', 'development'), DevelopmentConfig)

    # Configurations
    app.config.from_object(env_config)

    # HTTP error handling 404
    @app.errorhandler(404)
    def not_found_404(error=None):
        ''' Handle invalid URL '''
        message = {
            'status': 404,
            'message': 'Not found! This url: '+ request.url + ' is not provide!!'
        }
        resp = jsonify(message)
        return jsonify(message)

    # HTTP error handling 405
    @app.errorhandler(405)
    def not_found_405(error=None):
        ''' Handle invalid METHOD '''
        message = {
            'status': 405,
            'message': 'Method not allow at: '+ request.url
        }
        resp = jsonify(message)
        return resp


    # Initialize Plugins
    ma.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'site.loginPage'
    Bootstrap(app)


    with app.app_context():
        from .homesite import site
        from .api_user import user_api
        from .api_music import music_api


        # Register Blueprints
        app.register_blueprint(site)
        app.register_blueprint(user_api)
        app.register_blueprint(music_api)

        return app
