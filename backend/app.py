import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(
    __name__,
    static_folder=os.path.join(
        os.path.dirname(__file__),
        "..",
        "frontend"
    ),
    static_url_path=""
)

CORS(app)

from predictor import (
    profiles,
    predict_matchup
)


@app.route("/")
def home():
    return send_from_directory(
        app.static_folder,
        "index.html"
    )


@app.route("/teams")
def get_teams():

    teams = sorted(
        profiles["DISPLAY_NAME"]
        .unique()
        .tolist()
    )

    return jsonify(teams)


@app.route("/predict", methods=["POST"])
def predict():

    try:

        data = request.get_json()

        if (
            not data
            or "team_a" not in data
            or "team_b" not in data
        ):
            return jsonify(
                {"error": "Missing team_a or team_b"}
            ), 400

        result = predict_matchup(
            data["team_a"],
            data["team_b"]
        )

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": "Prediction failed"}), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )