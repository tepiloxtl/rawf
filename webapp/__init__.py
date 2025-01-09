from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)
app.config.from_object(Config)

from webapp import routes