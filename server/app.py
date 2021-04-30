from features.log.views import bp_log

from flask import Flask
app = Flask(__name__)

def create_app():
    with app.app_context():
        app.register_blueprint(bp_log, url_prefix="/api/log")
        return app

app = create_app()

app.register_blueprint(bp_log, url_prefix="/api/log")


if __name__ == '__main__':
    # app.run(host='127.0.0.1', debug=True, port=5000)
    app.run(host='0.0.0.0', debug=False, port=5001)





