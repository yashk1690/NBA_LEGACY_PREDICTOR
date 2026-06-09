from flask import Flask
from flask import jsonify
from flask import request

from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from predictor import (
    profiles,
    predict_matchup
)

app = Flask(__name__)


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

    data = request.get_json()

    team_a = data["team_a"]
    team_b = data["team_b"]

    result = predict_matchup(
        team_a,
        team_b
    )

    return jsonify(result)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )