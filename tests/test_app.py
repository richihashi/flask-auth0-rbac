import pytest
# importing from app.py
from app import create_app

# A fixture is just a setup function that runs before your tests and provides something your tests need.
# Think of it like prep work. Every test you write is going to need a Flask app and a test client to make requests. 
# Instead of creating those in every single test, you write the setup once as a fixture, and pytest automatically passes it to any test that asks for it.
# pytest.fixture is a pytest decorator. It tells pytest "this function provides something that tests need." creates this instance for each test to not have previous test mess with the new test
# pytest  knows it is a test function if the funciton name starts with 'test_' when client parameter is passed, pytest recognizes it needs a fixture called client and run it which makes the app.
@pytest.fixture
def app():
    # create the app
    app = create_app()
    # tells flask that it is for testing. won't print detailed error pages
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app):
    # test_client() is a flask method which gives you a fake browser — you can make GET and POST requests to your app without actually running the server.
    return app.test_client()

# test function test for code 200
# When pytest sees client as a parameter, it runs the client fixture to get the test client. Then client.get("/") simulates a GET request to / — same as visiting it in a browser, but without a real server running.
def test_home(client):
    response = client.get("/")
    assert response.status_code == 200

def login_session(client, roles=None):
    # flask method session_transaction, allows us to specify the test session variable for test app
    with client.session_transaction() as sess:
        sess["user"] = {
            "name": "test",
            "email": "test@example.com",
            "roles": roles or [],
        }

def test_dashboard_redirects_when_not_logged_in(client):
    response = client.get("/dashboard")
    # assert means this must be true otherwise test fails.
    assert response.status_code == 302

def test_dashboard_works_when_logged_in(client):
    login_session(client)
    response = client.get("/dashboard")
    assert response.status_code == 200

def test_admin_forbidden_without_role(client):
    login_session(client, ['viewer'])
    response = client.get("/admin")
    assert response.status_code == 302

def test_admin_works_with_role(client):
    login_session(client, ['admin'])
    response = client.get("/admin")
    assert response.status_code == 200

def test_api_public(client):
    response = client.get("/api/public")
    assert response.status_code == 200

def test_api_private_rejects_no_token(client):
    response = client.get("/api/private")
    assert response.status_code == 401

def test_api_private_rejects_bad_header(client):
    response = client.get("api/private", headers={"Authorization": "Basic abc"})
    assert response.status_code == 401

def test_security_headers(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"