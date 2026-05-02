# Flask Web App with Auth0 OIDC and RBAC
Basic web app created using Python Flask for studying learning OIDC integration using Auth0 and enforcing security using headers.

## Features:
- OIDC: Open ID Connect allows user authentication using third-party like Google. (resource owner is user, client is this web app, Auth server is Auth0, Idp could be google or anything that allows OIDC)
- RBAC: Role-based Acces Control enforced using Auth0. Certain routes are only accessible with admin role
- JWT API: API token used for private api routes. Only Bearer token can be used for private api route
- Security Headers: Enforcing security protecting using headers in the request/response. 
- Test Cases: Test cases built using pytest for basic testing

## Prerequisites:
- Python
- IDE
- Auth0 Account

## Auth0 Setup:
- Create an Account at https://auth0.auth0.com/
- Create Application - Regular Web App
- Change Allowed Callback URLs and Allowed Logout URLs in settings to http://127.0.0.1:5000/callback and http://127.0.0.1:5000
- Create admin and viewer roles in Roles under User Management
- Create a post-login action to add roles to the token used for authentication. Can be done at Triggers under Actions -
  ```javascript
  exports.onExecutePostLogin = async (event, api) => {
    const namespace = "https://flask-rbac-api";
    api.accessToken.setCustomClaim(namespace + "/roles", event.authorization.roles);
    api.idToken.setCustomClaim(namespace + "/roles", event.authorization.roles);
  };
  ```
- Create API - make sure it uses RS256 signing algorithm for token. API must be authorized for your application. Go to application -> API -> your API -> Edit your API -> allow access

## Installation:
- Clone the repo
- create venv
  ```
  python -m venv .venv
  ```
- install requirements from requirements.txt
  ```
  pip install -r requirements.txt
  ```
- set up .env file - follow the .env.example file to fill in the values

## Running:
- python app.py at the project root to run the app
- flask should tell you the IP in the terminal
- access the IP using browser

## Testing:
- From root project folder, run pytest -v
- runs through multiple test to verify authentication, rbac, and security headers are working

## Project Structure:
- `app.py` - creates web app using flask, contains 6 routes and 2 api routes
  - contains decorators requires_auth, requires_role, requires_api_auth
    - requires_auth requires users to be authenticated when accessing /dashboard route
    - requires_role requires role before accessing /admin route
    - requires_api_auth require a valid jwt token before accessing /api/private route
- `.env.example` - contains basic guidance for creating your own .env file
- `requirements.txt` - list all dependencies
- `tests` - contains test_app.py for test cases

For IaC-level OIDC project - https://github.com/richihashi/simple-aws-terraform-webserver 
This project handles OIDC at the application level with Python. The IaC project handles it at the infrastructure level with Apache and Terraform.
