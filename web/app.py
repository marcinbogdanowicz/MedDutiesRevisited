from flask import Flask, request
from pydantic import ValidationError

from algorithm.main import set_duties, validate_duties_can_be_set
from algorithm.translation import init_locale

app = Flask(__name__)


@app.before_request
def configure_locale():
    data = request.get_json(silent=True) or {}
    init_locale(data)


@app.errorhandler(ValidationError)
def handle_data_validation_error(e):
    return {"error": e.errors(include_url=False, include_input=False, include_context=False)}, 400


@app.errorhandler(404)
def not_found(e):
    return {"error": f"Not found: {request.url}"}, 404


@app.errorhandler(Exception)
def handle_server_error(e):
    app.logger.error(str(e))
    return {"error": "Something went wrong."}, 400


@app.post("/set_duties")
def handle_set_duties():
    data = request.get_json(silent=True)
    return set_duties(data)


@app.post("/validate_duties")
def handle_validating_duties():
    data = request.get_json(silent=True)
    return validate_duties_can_be_set(data)
