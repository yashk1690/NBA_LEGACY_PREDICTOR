import joblib
import numpy as np
import pandas as pd

# ─────────────────────────────────────────
# Load regular model
# ─────────────────────────────────────────

bundle = joblib.load(
    "models/nba_historical_simulator.pkl"
)

model         = bundle["model"]
feature_order = bundle["features"]

profiles = pd.read_csv("data/team_profiles_v3.csv")

profiles["DISPLAY_NAME"] = (
    profiles["SEASON_STR"]
    + " | "
    + profiles["TEAM_NAME"]
)

# ─────────────────────────────────────────
# Load playoff models
# ─────────────────────────────────────────

playoff_bundle = joblib.load(
    "models/nba_playoff_simulator.pkl"
)
playoff_model         = playoff_bundle["model"]
playoff_feature_order = playoff_bundle["features"]

playoff_bundle_2 = joblib.load(
    "models/nba_playoff_simulator_2.pkl"
)
playoff_model_2         = playoff_bundle_2["model"]
playoff_feature_order_2 = playoff_bundle_2["features"]

playoff_profiles = pd.read_csv("data/playoff_team_profiles_v3.csv")

playoff_profiles["DISPLAY_NAME"] = (
    playoff_profiles["SEASON_STR"]
    + " | "
    + playoff_profiles["TEAM_NAME"]
)

# ─────────────────────────────────────────
# Team lookup
# ─────────────────────────────────────────

def get_team_profile(display_name):

    row = profiles[
        profiles["DISPLAY_NAME"] == display_name
    ]

    if len(row) == 0:
        raise ValueError(f"Team not found: {display_name}")

    return row.iloc[0]


def get_playoff_team_profile(display_name):

    row = playoff_profiles[
        playoff_profiles["DISPLAY_NAME"] == display_name
    ]

    if len(row) == 0:
        raise ValueError(
            f"Playoff team not found: {display_name}"
        )

    return row.iloc[0]


# ─────────────────────────────────────────
# Feature configuration
# ─────────────────────────────────────────

FEATURE_MAP = {
    "fg_pct_matchup_diff":               "fg_pct",
    "opp_fg_pct_matchup_diff":           "opp_fg_pct",
    "fg3_pct_matchup_diff":              "fg3_pct",
    "opp_fg3_pct_matchup_diff":          "opp_fg3_pct",
    "ft_pct_matchup_diff":               "ft_pct",
    "reb_matchup_diff":                  "reb",
    "ast_matchup_diff":                  "ast",
    "stl_matchup_diff":                  "stl",
    "blk_matchup_diff":                  "blk",
    "tov_matchup_diff":                  "tov",
    "assist_turnover_ratio_matchup_diff": "assist_turnover_ratio",
    "reb_diff_matchup_diff":             "reb_diff",
    "ast_diff_matchup_diff":             "ast_diff",
    "tov_diff_matchup_diff":             "tov_diff",
    "pace_matchup_diff":                 "pace",
    "ortg_matchup_diff":                 "ortg",
    "drtg_matchup_diff":                 "drtg",
    "efg_pct_matchup_diff":              "efg_pct",
    "ts_pct_matchup_diff":               "ts_pct"
}

FEATURE_DISPLAY_NAMES = {
    "fg_pct_matchup_diff":               "Field Goal %",
    "opp_fg_pct_matchup_diff":           "Opp. Field Goal % (Defense)",
    "fg3_pct_matchup_diff":              "3-Point %",
    "opp_fg3_pct_matchup_diff":          "Opp. 3-Point % (Defense)",
    "ft_pct_matchup_diff":               "Free Throw %",
    "reb_matchup_diff":                  "Rebounds",
    "ast_matchup_diff":                  "Assists",
    "stl_matchup_diff":                  "Steals",
    "blk_matchup_diff":                  "Blocks",
    "tov_matchup_diff":                  "Turnovers",
    "assist_turnover_ratio_matchup_diff": "Assist / Turnover Ratio",
    "reb_diff_matchup_diff":             "Rebound Margin",
    "ast_diff_matchup_diff":             "Assist Margin",
    "tov_diff_matchup_diff":             "Turnover Margin",
    "pace_matchup_diff":                 "Pace",
    "ortg_matchup_diff":                 "Offensive Rating",
    "drtg_matchup_diff":                 "Defensive Rating",
    "efg_pct_matchup_diff":              "Effective FG %",
    "ts_pct_matchup_diff":               "True Shooting %"
}

# Lower value = better for the team
LOWER_IS_BETTER = {
    "drtg_matchup_diff",
    "tov_matchup_diff",
    "tov_diff_matchup_diff",
    "opp_fg_pct_matchup_diff",
    "opp_fg3_pct_matchup_diff"
}

# Stored as decimals; multiply ×100 for percentage points
PCT_FEATURES = {
    "fg_pct_matchup_diff",
    "opp_fg_pct_matchup_diff",
    "fg3_pct_matchup_diff",
    "opp_fg3_pct_matchup_diff",
    "ft_pct_matchup_diff",
    "efg_pct_matchup_diff",
    "ts_pct_matchup_diff"
}


# ─────────────────────────────────────────
# Feature vector builders
# ─────────────────────────────────────────

def build_feature_vector(team_a, team_b):
    """Regular model — uses explicit FEATURE_MAP."""

    features = {}

    for matchup_feat, profile_col in FEATURE_MAP.items():
        features[matchup_feat] = (
            float(team_a[profile_col])
            - float(team_b[profile_col])
        )

    return features


def build_dynamic_feature_vector(team_a, team_b, feat_order):
    """
    Playoff models — derives column name by stripping
    '_matchup_diff', handles any extra features automatically.
    """

    features = {}

    for feat in feat_order:
        col = feat.replace("_matchup_diff", "")
        try:
            features[feat] = (
                float(team_a[col]) - float(team_b[col])
            )
        except (KeyError, ValueError):
            features[feat] = 0.0

    return features


# ─────────────────────────────────────────
# Home-court bias correction
# ─────────────────────────────────────────

def get_neutral_prob(m, X):
    """
    The models carry a home-team bias from training data.
    Fix: run the prediction both ways and average.

      P(A wins | A listed first)   →  prob_ab
      P(B wins | B listed first)   →  prob_ba
      P(A wins | B listed first)   →  1 - prob_ba

    Neutral P(A wins) = (prob_ab + (1 - prob_ba)) / 2

    The reversed feature vector is simply X * -1, because
    all features are (A - B) diffs; flipping gives (B - A).
    """

    prob_ab = float(m.predict_proba(X)[0, 1])
    prob_ba = float(m.predict_proba(X * -1)[0, 1])

    return (prob_ab + (1 - prob_ba)) / 2


# ─────────────────────────────────────────
# Top factors
# ─────────────────────────────────────────

def clean_feature_name(feat):
    return (
        feat.replace("_matchup_diff", "")
            .replace("_", " ")
            .title()
    )


def get_top_factors(
    feature_vector,
    team_a_name,
    team_b_name,
    winner,
    n=5
):
    """
    Top n stats where the predicted winner holds the
    largest advantage, sorted by absolute differential.
    """

    factors = []

    for feat, value in feature_vector.items():

        lower_is_better = feat in LOWER_IS_BETTER

        team_a_favored = (
            (value > 0 and not lower_is_better)
            or (value < 0 and lower_is_better)
        )

        if feat in PCT_FEATURES:
            display_value = f"{abs(value * 100):.1f} pp"
        else:
            display_value = f"{abs(value):.1f}"

        advantage = team_a_name if team_a_favored else team_b_name

        factors.append({
            "stat":      FEATURE_DISPLAY_NAMES.get(
                             feat, clean_feature_name(feat)
                         ),
            "value":     display_value,
            "advantage": advantage,
            "_abs":      abs(value)
        })

    factors.sort(key=lambda x: x["_abs"], reverse=True)

    winning_factors = [
        f for f in factors if f["advantage"] == winner
    ]

    return [
        {k: v for k, v in f.items() if k != "_abs"}
        for f in winning_factors[:n]
    ]


# ─────────────────────────────────────────
# Single game (10,000 simulations)
# ─────────────────────────────────────────

def predict_matchup(
    team_a_name,
    team_b_name,
    n_simulations=10_000
):

    team_a = get_team_profile(team_a_name)
    team_b = get_team_profile(team_b_name)

    feature_vector = build_feature_vector(team_a, team_b)

    X = pd.DataFrame([feature_vector])[feature_order]

    # Bias-corrected probability
    prob = get_neutral_prob(model, X)

    # Monte-Carlo game simulations
    rng = np.random.default_rng()
    sim_wins_a = int(np.sum(rng.random(n_simulations) < prob))

    winner = team_a_name if prob >= 0.5 else team_b_name

    top_factors = get_top_factors(
        feature_vector, team_a_name, team_b_name, winner
    )

    return {
        "team_a":                 team_a_name,
        "team_b":                 team_b_name,
        "team_a_win_probability": prob,
        "team_b_win_probability": 1 - prob,
        "team_a_sim_wins":        sim_wins_a,
        "team_b_sim_wins":        n_simulations - sim_wins_a,
        "total_simulations":      n_simulations,
        "winner":                 winner,
        "top_factors":            top_factors
    }


# ─────────────────────────────────────────
# Playoff series (10,000 series)
# ─────────────────────────────────────────

def predict_playoff_series(
    team_a_name,
    team_b_name,
    model_id=1,
    n_simulations=10_000
):

    # Select model by id
    if model_id == 2:
        m          = playoff_model_2
        feat_order = playoff_feature_order_2
    else:
        m          = playoff_model
        feat_order = playoff_feature_order

    team_a = get_playoff_team_profile(team_a_name)
    team_b = get_playoff_team_profile(team_b_name)

    feature_vector = build_dynamic_feature_vector(
        team_a, team_b, feat_order
    )

    X = pd.DataFrame([feature_vector])[feat_order]

    # Bias-corrected per-game probability
    game_prob = get_neutral_prob(m, X)

    # ── Simulate 10,000 best-of-7 series ──────────────

    rng = np.random.default_rng()

    series_wins_a  = 0
    length_counts  = {4: 0, 5: 0, 6: 0, 7: 0}
    outcome_counts = {}

    for _ in range(n_simulations):

        wa, wb = 0, 0

        while wa < 4 and wb < 4:
            if rng.random() < game_prob:
                wa += 1
            else:
                wb += 1

        if wa == 4:
            series_wins_a += 1
            key = f"4-{wb}"
        else:
            key = f"{wa}-4"

        length_counts[wa + wb] += 1
        outcome_counts[key] = outcome_counts.get(key, 0) + 1

    # ── Format outputs ─────────────────────────────────

    series_prob_a = series_wins_a / n_simulations

    expected_games = sum(
        g * c / n_simulations
        for g, c in length_counts.items()
    )

    length_pcts = {
        str(g): round(c / n_simulations * 100, 1)
        for g, c in sorted(length_counts.items())
    }

    outcome_pcts = {
        k: round(v / n_simulations * 100, 1)
        for k, v in sorted(
            outcome_counts.items(),
            key=lambda x: -x[1]
        )
    }

    winner = team_a_name if series_prob_a >= 0.5 else team_b_name

    top_factors = get_top_factors(
        feature_vector, team_a_name, team_b_name, winner
    )

    return {
        "team_a":              team_a_name,
        "team_b":              team_b_name,
        "game_win_prob_a":     round(game_prob * 100, 1),
        "game_win_prob_b":     round((1 - game_prob) * 100, 1),
        "series_win_prob_a":   round(series_prob_a * 100, 1),
        "series_win_prob_b":   round((1 - series_prob_a) * 100, 1),
        "winner":              winner,
        "expected_games":      round(expected_games, 1),
        "length_distribution": length_pcts,
        "series_outcomes":     outcome_pcts,
        "total_simulations":   n_simulations,
        "top_factors":         top_factors
    }