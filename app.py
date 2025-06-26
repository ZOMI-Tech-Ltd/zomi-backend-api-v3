from flask import Flask
from config import Config
from extensions import init_extensions, db
from routes.dish import dish_bp
from routes.user_actions import user_actions_bp
from flask import jsonify
from sqlalchemy.orm import configure_mappers
from models.like import Like

from models.dish import Dish
from models.merchant import Merchant
from models.media import Media
from models.taste import Taste
from models.collection import Collection
from models.user import User
from models.dish_profile import DishProfile
from utils.response_utils import create_response

from models.thirdparty import ThirdPartyDelivery

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    #initialize extensions
    init_extensions(app)

    app.register_blueprint(dish_bp)
    app.register_blueprint(user_actions_bp)


    @app.errorhandler(404)
    def not_found(error):
        return create_response(code=404, message='Not found'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return create_response(code=500, message='Internal server error'), 500


    with app.app_context(): 
        configure_mappers()
    return app


app = create_app()


if __name__ == '__main__':                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
    app.run(debug=True, host='0.0.0.0', port=4003)
