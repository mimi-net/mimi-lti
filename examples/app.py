import os

from flask import Flask
from controllers import login, launch, get_jwks, create_test, get_grade, set_grade


app = Flask(__name__)


app.config["SECRET_KEY"] = os.urandom(16).hex()
app.config["SESSION_COOKIE_NAME"] = "mimilti_session"
app.add_url_rule("/login", methods=["GET", "POST"], view_func=login)
app.add_url_rule("/launch", methods=["GET", "POST"], view_func=launch)
app.add_url_rule("/jwks", methods=["GET", "POST"], view_func=get_jwks)
app.add_url_rule("/set_grade", methods=["GET", "POST"], view_func=set_grade)
app.add_url_rule("/create_test", methods=["GET", "POST"], view_func=create_test)
app.add_url_rule("/get_grade", methods=["GET", "POST"], view_func=get_grade)


@app.route("/")
def index():
    return ""


if __name__ == "__main__":
    app.run(port=9002)
