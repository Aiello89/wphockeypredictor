from flask import Flask, render_template, request
import pandas as pd
import math

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

# Define the weights for each factor in the final probability calculation
situation_weights = {
    "4v5 PK": 0.1,
    "5v4 PP": 0.15,
    "5v5": 0.4,
    "5v5 Score & VA": 0.15,
    "Even Strength": 0.2,
}

# Define the weights for other factors
recent_games_weight = 0.2
home_ice_advantage_weights = {"Team 1_Away": 0.45, "Team 2_Home": 0.55}
back_to_back_weights = {"yes": -0.25, "no": 0}

situations = list(situation_weights.keys())

def calculate_weighted_average(stats):
    weighted_stats = {}
    for team, team_stats in stats.items():
        weighted_stats[team] = {}
        for stat, weight in weights.items():
            weighted_stats[team][stat] = team_stats[stat] * weight
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

def calculate_final_probabilities(combined_implied_probs, situation_weights):
    final_probs = {}
    for team in combined_implied_probs[situations[0]].keys():  # Use the first situation to get the team keys
        final_probs[team] = sum(situation_weights[situation] * combined_implied_probs[situation][team] for situation in situations)

    # Normalize the final probabilities
    sum_probs = sum(final_probs.values())
    norm_probs = {team: final_probs[team] / sum_probs for team in final_probs.keys()}

    return norm_probs

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def calculate_probabilities():
    team1_stats = {}
    team2_stats = {}
    team1_cf = request.form.get("team1_CF%", "0")
    team2_cf = request.form.get("team2_CF%", "0")
    print("team1_CF:", team1_cf)
    print("team2_CF:", team2_cf)
    team1_ff = request.form.get("team1_FF%", "0")
    team2_ff = request.form.get("team2_FF%", "0")
    print("team1_FF:", team1_ff)
    print("team2_FF:", team2_ff)
    team1_xgf = request.form.get("team1_xGF%", "0")
    team2_xgf = request.form.get("team2_xGF%", "0")
    print("team1_xGF:", team1_xgf)
    print("team2_xGF:", team2_xgf)
    team1_hdcf = request.form.get("team1_HDCF%", "0")
    team2_hdcf = request.form.get("team2_HDCF%", "0")
    print("team1_hdcf:", team1_hdcf)
    print("team2_hdcf:", team2_hdcf)
    team1_hdsf = request.form.get("team1_HDSF%", "0")
    team2_hdsf = request.form.get("team2_HDSF%", "0")
    print("team1_hdsf:", team1_hdsf)
    print("team2_hdsf:", team2_hdsf)
    team1_pdo = request.form.get("team1_PDO", "0")
    team2_pdo = request.form.get("team2_PDO", "0")
    print("team1_pdo:", team1_pdo)
    print("team2_pdo:", team2_pdo)

    # define a dictionary to store the values for each team for each stat
    values = {}

    # define a list of stats
    stats = ["CF%", "FF%", "xGF%", "HDCF%", "HDSF%", "PDO"]
  
    for stat in stats:
        team1_stat_str = request.form[f"team1_{stat}"]
        team2_stat_str = request.form[f"team2_{stat}"]

        team1_stat = float(team1_stat_str)
        team2_stat = float(team2_stat_str)
        values[stat] = {
            "team1": team1_stat,
            "team2": team2_stat
        }

    for stat in stats:
        print("Value1 for " + stat + ":", values[stat]["team1"])
        print("Value2 for " + stat + ":", values[stat]["team2"])

    for situation in situations:
        team1_stats[situation] = {}
        team2_stats[situation] = {}
        for key in weights.keys():
            value1 = request.form.get(f"team1_{situation.replace(' ', '_')}_{key}", "0")
            value2 = request.form.get(f"team2_{situation.replace(' ', '_')}_{key}", "0")
            team1_stats[situation][key] = float(value1) if value1 != '' else 0
            team2_stats[situation][key] = float(value2) if value2 != '' else 0
            print(f"Value1 for {situation}/{key}: {value1}")
            print(f"Value2 for {situation}/{key}: {value2}")

    # Check if any of the input values are zero or less
    if any(value <= 0 for stats in [team1_stats, team2_stats] for values in stats.values() for value in values.values()):
        return "Error: Input values must be greater than zero."
    
    # Check if the value is greater than zero
        if float(value1) <= 0:
            value1 = "0.01"  # set a small positive value
        if float(value2) <= 0:
            value2 = "0.01"  # set a small positive value

    weighted_stats = {}
    implied_probs = {}
    combined_implied_probs = {}

    for situation in situations:
        weighted_stats[situation] = calculate_weighted_average({"Team 1_Away": team1_stats[situation], "Team 2_Home": team2_stats[situation]})
        print(f"Weighted Stats for {situation}: {weighted_stats[situation]}")
        implied_probs[situation] = calculate_implied_probabilities(weighted_stats[situation])
        print(f"Implied Probs for {situation}: {implied_probs[situation]}")
        implied_probs_df = pd.DataFrame(implied_probs[situation]).T
        combined_implied_probs[situation] = calculate_combined_implied_probabilities(implied_probs_df)
        print(f"Combined Implied Probs for {situation}: {combined_implied_probs[situation]}")

    final_probs = calculate_final_probabilities(combined_implied_probs, situation_weights)
    print(f"Final Probs before other factors: {final_probs}")

    # Incorporate other factors
    team1_recent_games_weight = float(request.form.get("team1_recent_games_weight", "0"))
    team2_recent_games_weight = float(request.form.get("team2_recent_games_weight", "0"))
    team1_back_to_back = request.form.get("team1_back_to_back", "no")
    team2_back_to_back = request.form.get("team2_back_to_back", "no")
    print(f"Final Probs after other factors: {final_probs}")

    # Check for NaN values
    if any(math.isnan(value) for value in final_probs.values()):
        return "Error: Final probabilities contain NaN values."

    final_probs["Team 1_Away"] = (
        0.7 * final_probs["Team 1_Away"]
        + 0.2 * team1_recent_games_weight
        + 0.05 * home_ice_advantage_weights["Team 1_Away"]
        + 0.05 * back_to_back_weights[team1_back_to_back]
    )
    final_probs["Team 2_Home"] = (
        0.7 * final_probs["Team 2_Home"]
        + 0.2 * team2_recent_games_weight
        + 0.05 * home_ice_advantage_weights["Team 2_Home"]
        + 0.05 * back_to_back_weights[team2_back_to_back]
    )
    print(f"Final Probs after other factors: {final_probs}")

    print("Final Probs:", final_probs)
    print("Sum of Probs:", sum_probs)

    if sum_probs > 0:
        norm_probs = {team: final_probs[team] / sum_probs for team in final_probs.keys()}
    else:
        norm_probs = final_probs

    # Normalize the final probabilities
    sum_probs = sum(final_probs.values())
    print("Final Probs:", final_probs)
    print("Sum of Probs:", sum_probs)

    norm_probs = {team: final_probs[team] / sum_probs for team in final_probs.keys()}

    return render_template("results.html", final_probs=norm_probs)

if __name__ == "__main__":
    app.run(debug=True)
