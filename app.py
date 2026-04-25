from flask import Flask, redirect, session, url_for
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from functools import wraps
import os

# load the .env file and makes the values available through os.getenv("")
load_dotenv()

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # check if user is logged in
        if "user" not in session:
            return redirect(url_for("login"))
        
        return f(*args, **kwargs)
    return decorated

def create_app():
    # initialize flask app, __name__ tells Flask where to find your project files.
    app = Flask(__name__)

    # Setting secret key and configs for auth0 for the app
    app.secret_key = os.getenv("FLASK_SECRET_KEY")
    app.config["AUTH0_DOMAIN"] = os.getenv("AUTH0_DOMAIN")
    app.config["AUTH0_CLIENT_ID"] = os.getenv("AUTH0_CLIENT_ID")
    app.config["AUTH0_CLIENT_SECRET"] = os.getenv("AUTH0_CLIENT_SECRET")

    # create OAuth instance and connect it to app
    oauth = OAuth(app)

    # registering oauth as a provider, telling authlib library everything it needs to know about our auth0 instance
    oauth.register("auth0", 
                   client_id = app.config["AUTH0_CLIENT_ID"], 
                   client_secret = app.config["AUTH0_CLIENT_SECRET"], 
                   # this part tells auth0 what info we are requesting, openid for OIDC, profile is the user's name, and email is their email
                   client_kwargs = {"scope": "openid profile email"}, 
                   server_metadata_url = "https://" + app.config["AUTH0_DOMAIN"] + "/.well-known/openid-configuration")

    # Route 1: Home page
    @app.route("/")
    def home():
        return "Welcome user"
    
    # Route 2: Dashboard (placeholder for now)
    @app.route("/dashboard")
    @requires_auth
    def dashboard():
        return "Welcome to Dashboard"
    
    # Route 3: Redirect user to Auth0
    @app.route("/login")
    def login():
        # authorize_redirect builds the callbackurl, where auth0 should return the user, and redirect the user to auth0, passing the callback url along. url_for() builds urls for your routes by name.
        return oauth.auth0.authorize_redirect(url_for("callback", _external=True))

    # Route 4: Auth0 redirect user after they login
    @app.route("/callback")
    def callback():
        # exchange the authorization code for tokens (Id token, access token)
        token = oauth.auth0.authorize_access_token()
        # get the user info from token and store it in session to app remembers who is logged in
        session["user"] = token["userinfo"]
        # redirect the user to the dashboard
        return redirect(url_for("dashboard"))

    # Route 5: Logout, clear session and redirect to auth0's logout endpoint
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("https://" + app.config["AUTH0_DOMAIN"] + "/v2/logout?returnTo=" + url_for("home", _external=True) + "&client_id=" + app.config["AUTH0_CLIENT_ID"])
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)