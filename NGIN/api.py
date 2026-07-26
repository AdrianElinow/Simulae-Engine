from pathlib import Path

from flask import Flask, jsonify
from flask_cors import CORS
from NGIN.NGIN import NGIN
from NGIN.utilities.lib.ngin_utils import load_json_from_file


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
ALLOWED_ORIGINS = ["http://127.0.0.1:5173", "http://localhost:5173"]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(TESTING=False)
    if test_config:
        app.config.update(test_config)

    CORS(app, resources={r"/api/*": {"origins": ALLOWED_ORIGINS}})

    @app.get("/api")
    def index():
        return jsonify({
            "message": "NGIN Campaign Generator API is running.",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/generate_campaign",
                    "summary": "Generate a new campaign world state.",
                }
            ],
        })

    @app.get("/api/generate_campaign")
    def generate_campaign():
        mission_struct = load_json_from_file(
            "NGIN_config/story_struct.json", filepath=str(REPOSITORY_ROOT / "NGIN")
        )
        ngin_settings = load_json_from_file(
            "NGIN_config/ngin_settings.json", filepath=str(REPOSITORY_ROOT / "NGIN")
        )

        ngin = NGIN(mission_struct, ngin_settings, is_console=False)
        return jsonify(ngin.state.toJSON())

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
