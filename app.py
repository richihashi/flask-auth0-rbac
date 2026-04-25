from flask import Flask

def create_app():
    # initialize flask app, __name__ tells Flask where to find your project files.
    app = Flask(__name__)

    # Route 1: Home page
    @app.route("/")
    def home():
        return "Welcome user!"
    
    # Route 2: Dashboard (placeholder for now)
    @app.route("/dashboard")
    def dashboard():
        return "Welcome to Dashboard"
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)