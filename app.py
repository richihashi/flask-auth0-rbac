from flask import Flask, redirect, session, url_for, request, jsonify, g
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth
from functools import wraps
from jose import jwt as jose_jwt
import os
import jwt
import requests

# load the .env file and makes the values available through os.getenv("")
load_dotenv()

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
                   client_kwargs = {"scope": "openid profile email",
                                    "audience": os.getenv("AUTH0_AUDIENCE")}, 
                   server_metadata_url = "https://" + app.config["AUTH0_DOMAIN"] + "/.well-known/openid-configuration",
                   # just adds api route
                   authorize_params={"audience": os.getenv("AUTH0_AUDIENCE")},)
    
    # helper funciton, f is the function that comes after this decorater, so for this app dashboard
    def requires_auth(f):
        # safeguard to make flask remembers the original function name
        @wraps(f)
        # new function decorated will replace dashbaord. *args and **kwargs accepts whatever argumetns the original function accepts
        def decorated(*args, **kwargs):
            # check if user is logged in
            if "user" not in session:
                return redirect(url_for("login"))
            # runs the check, and if it passes call f() which is the original funciton in the app example dashboard
            return f(*args, **kwargs)
        # return the new wrapped version
        return decorated

    # helper funciton, check for the role and redirect to right page if user lacks it
    def requires_role(role):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                if "user" not in session:
                    return redirect(url_for("login"))
                if role not in session["user"]["roles"]:
                    return redirect(url_for("home"))
                return f(*args, **kwargs)
            return decorated
        return decorator
    
    # get private key from auth0 domain for api token verification
    def get_jwks():
       url = "https://" + app.config["AUTH0_DOMAIN"] + "/.well-known/jwks.json"
       # makes a get request to the url
       response = requests.get(url)
       # return response in json format
       return response.json()
    
    # validates api token
    def validate_access_token(token):
        jwks = get_jwks()
        # get token headers, get_unverified_header function from jose can look at the header without verifying - we can get kid(key id) which tells which key was used to sign it
        unverified_header = jose_jwt.get_unverified_header(token)

        rsa_key = None
        # since jwks stores multiple keys, we are looping through them to find the key that matches for verification
        for key in jwks['keys']:
            if unverified_header['kid'] == key['kid']:
                rsa_key = key

        # throws an error if key was not found
        if not rsa_key:
            raise Exception("Unable to find matching key")
        
        # jose_jwt.decode ddoes everything, decodes the jwt token, checks signature, expiration, audience and issuer
        payload = jose_jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience = os.getenv("AUTH0_AUDIENCE"),
            issuer = "https://" + os.getenv("AUTH0_DOMAIN") + "/",
            )
        
        return payload
    
    # helper function, require api authentication
    def requires_api_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # flask request library headers function allow us to get headers
            auth_header = request.headers.get("Authorization", "")

            # checks if authorizaation header starts with Bearer
            if not auth_header.startswith("Bearer "):
                # Flask returns json data with an error code 401 - flask specific
                return jsonify({"error": "No API token"}), 401
            
            # splits the Bearer token 'Bearer xxxx.yyyy.zzzz' with space at most once so index 0 becomes bearer and index 1 becomes token and just return the token as var token
            token = auth_header.split(" ", 1)[1]

            # try to get the payload from the token
            try:
                payload = validate_access_token(token)
            except Exception as e:
                # return error if it fails
                return jsonify({"error": str(e)}), 401
            
            # g is a flask object that acts as temporary storage during a single request. It is like session but only for one request. no need to return or clean as Flask handles it
            g.current_user = payload
            
            return f(*args, **kwargs)
        return decorated


    # Route 1: Home page
    @app.route("/")
    def home():
        return "Welcome user"
    
    # Route 2: Dashboard (placeholder for now)
    @app.route("/dashboard")
    @requires_auth
    def dashboard():
        #for debugging with callback
        # return str(session["user"])
        return "Welcome to Dashboard. Your roles: " + str(session["user"].get("roles", []))
    
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
        # decode the access token
        decoded = jwt.decode(token["access_token"], options={"verify_signature": False})
        # get the roles from the user
        roles = decoded.get("https://flask-rbac-api/roles", [])
        # set the user variable for session to a dictionary of userinfo
        session["user"] = dict(token["userinfo"])
        # set the roles key with roles value gotten from token
        session["user"]["roles"] = roles

        # debug code
        # session["user"] = token["access_token"]

        # redirect the user to the dashboard
        return redirect(url_for("dashboard"))

    # Route 5: Logout, clear session and redirect to auth0's logout endpoint
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("https://" + app.config["AUTH0_DOMAIN"] + "/v2/logout?returnTo=" + url_for("home", _external=True) + "&client_id=" + app.config["AUTH0_CLIENT_ID"])
    
    # Route 6: admin panel where only user with admin role have access
    @app.route("/admin")
    @requires_role("admin")
    def admin():
        return "Welcome" + str(session["user"])
    
    # Route 7: API route public for testing
    @app.route("/api/public")
    def api_public():
        return jsonify({"message": "This is a public endpoint, no auth required"})
    
    # Route 8: API route private for testing tokens
    @app.route("/api/private")
    @requires_api_auth
    def api_private():
        # get current_user decode token payload from g and get sub (subject claim) which is unique user ID. .get returns None if key doesn't exist instead of crashing
        return jsonify({"message": "You have a valid token", "user": g.current_user.get("sub")})
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)