from flask import Flask, request
from pydantic import ValidationError

app = Flask(__name__)


@app.route("/")
def index():
    return {"message": "Welcome to the DUTY SCHEDULER API!"}


@app.post("/set_duties")
def set_duties():
    from algorithm.main import main

    try:
        return main(request.get_json())
    except ValidationError as e:
        return {"error": e.errors(include_url=False, include_input=False, include_context=False)}, 400
    except Exception as e:
        app.logger.error(str(e))
        return {"error": "Something went wrong."}, 400


@app.errorhandler(404)
def not_found(e):
    return {"error": f"Not found: {request.url}"}, 404
