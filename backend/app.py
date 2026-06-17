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
    playoff_profiles,
    predict_matchup,
    predict_playoff_series
)

from similarity import (
    get_cluster_teams,
    find_similar_teams
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


@app.route("/playoff_teams")
def get_playoff_teams():

    teams = sorted(
        playoff_profiles["DISPLAY_NAME"]
        .unique()
        .tolist()
    )

    return jsonify(teams)


@app.route("/cluster_teams")
def cluster_teams():
    return jsonify(get_cluster_teams())


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


@app.route("/predict_series", methods=["POST"])
def predict_series():

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

        result = predict_playoff_series(
            data["team_a"],
            data["team_b"],
            model_id=int(data.get("model_id", 1))
        )

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": "Series prediction failed"}), 500


@app.route("/similar", methods=["POST"])
def similar():

    try:

        data = request.get_json()

        if not data or "team" not in data:
            return jsonify({"error": "Missing team"}), 400

        result = find_similar_teams(
            data["team"],
            n=int(data.get("n", 10))
        )

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 404

    except Exception as e:
        return jsonify({"error": "Similarity search failed"}), 500


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )