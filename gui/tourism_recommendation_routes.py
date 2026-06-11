from gui.tourism_recommendation_admin_routes import register_recommendation_admin_routes
from gui.tourism_recommendation_user_routes import register_recommendation_user_routes


def register_tourism_recommendation_routes(app):
    if app.config.get('FAY_TOURISM_RECOMMENDATION_ROUTES_REGISTERED'):
        return
    app.config['FAY_TOURISM_RECOMMENDATION_ROUTES_REGISTERED'] = True
    register_recommendation_user_routes(app)
    register_recommendation_admin_routes(app)
