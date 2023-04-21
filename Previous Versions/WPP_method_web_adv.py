from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)

# Define the weights for each key stat
weights = {
    "CF%": 0.15,
    "FF%": 0.15,
    "xGF%": 0.25,
    "HDCF%": 0.20,
    "HDSF%": 0.10,
    "PDO": 0.15,
}

# Define situations_weights
situations_weights = {
    "4v5 PK": 0.1,
    "5v4 PP": 0.15,
    "5v5": 0.4,
    "5v5 Score & VA": 0.10,
    "Even Strength": 0.20,
    "All_Sit": 0.05,
}

# Define the weights for each factor in the final probability calculation
overall_weight = 1
last_5_games_weight = 0.20
home_ice_advantage_weight = 0.05
back_2_back_weight = 0.05


def calculate_weighted_average(team_stats):
    total_weight = sum(team_stats.values())
    if total_weight == 0:
        return {team: 0.5 for team in team_stats}

    weighted_stats = {}
    for team, stat in team_stats.items():
        weighted_stats[team] = stat / total_weight
    return weighted_stats


def calculate_implied_probabilities(weighted_stats):
    implied_probs = {}
    for team, team_stats in weighted_stats.items():
        implied_probs[team] = {}
        for stat, value in team_stats.items():
            if stat == "PDO":
                value = 1 + ((value - 1000) / 1000)
            implied_probs[team][stat] = value / (value + 1)
    return implied_probs


def calculate_combined_implied_probabilities(implied_probs_df):
    combined_probs = {}
    for team in implied_probs_df.index:
        combined_prob = 1
        for stat in implied_probs_df.columns:
            combined_prob *= implied_probs_df.loc[team, stat]
        combined_probs[team] = combined_prob
    return combined_probs


def calculate_final_probabilities(combined_implied_probs, team_last_5_games, home_team_back_2_back):
    final_probs = {}
    for team in combined_implied_probs.keys():
        # Apply last 5 games weight
        team_last_5 = team_last_5_games.get(team, {"W": 0, "L": 0})
        last_5_games_ratio = team_last_5["W"] / (team_last_5["W"] + team_last_5["L"]) if (team_last_5["W"] + team_last_5["L"]) != 0 else 0.5
        last_5_games_weighted = last_5_games_ratio * last_5_games_weight

        # Apply home ice advantage weight
        home_ice_advantage_weighted = home_ice_advantage_weight if team == "Team 2" else 0

        # Apply back-to-back game deduction
        back_2_back_weighted = -back_2_back_weight if home_team_back_2_back[team] else 0

        final_probs[team] = overall_weight * combined_implied_probs[team] + last_5_games_weighted + home_ice_advantage_weighted + back_2_back_weighted

    # Normalize the final probabilities
    sum_probs = sum(final_probs.values())
    norm_probs = {team: final_probs[team] / sum_probs for team in final_probs.keys()}

    return norm_probs

@app.route("/")
def index():
    return render_template("index.html")

def safe_int(value, default=0):
    try:
        return int(value)
    except ValueError:
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except ValueError:
        return default

def calculate_probabilities(form):
    selected_situations = list(weights.keys())

    team1_stats = {stat: safe_float(form.get(f'team1_{stat}', 0)) for stat in weights.keys()}
    team2_stats = {stat: safe_float(form.get(f'team2_{stat}', 0)) for stat in weights.keys()}

    team1_filtered_stats = {sit: team1_stats[sit] * weights[sit] for sit in selected_situations if sit in weights}
    team2_filtered_stats = {sit: team2_stats[sit] * weights[sit] for sit in selected_situations if sit in weights}

    weighted_team1_stats = sum(team1_filtered_stats.values())
    weighted_team2_stats = sum(team2_filtered_stats.values())

    total_weight = sum(situations_weights.values())

    team1_final_prob = weighted_team1_stats / (weighted_team1_stats + weighted_team2_stats)
    team2_final_prob = weighted_team2_stats / (weighted_team1_stats + weighted_team2_stats)

    final_probs = {
        "team1_prob": team1_final_prob,
        "team2_prob": team2_final_prob
    }

    team1_last_5_games = [int(form.get("team1_last5_wins", 0)), int(form.get("team1_last5_losses", 0))]
    team2_last_5_games = [int(form.get("team2_last5_wins", 0)), int(form.get("team2_last5_losses", 0))]

    team_last_5_games = {
"team1_last_5_games": team1_last_5_games,
    "team2_last_5_games": team2_last_5_games
}

    home_team_back_2_back = form.get("home_team_back_2_back", False)

        return final_probs, team_last_5_games, home_team_back_2_back


@app.route("/upload", methods=["POST"])
def upload():
    final_probs, team_last_5_games, home_team_back_2_back = calculate_probabilities(request.form)

    return render_template(
    "results.html", 
    final_probs=final_probs, 
    last_5_games=team_last_5_games,
    b2b_games=home_team_back_2_back,
    home_advantage=home_ice_advantage_weight,
)

if __name__ == "__main__":
    app.run(debug=True)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))


