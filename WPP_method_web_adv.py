from flask import Flask, render_template, request
import pandas as pd

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
overall_weight = 1
last_5_games_weight = 0.20
home_ice_advantage_weight = 0.05
back_2_back_weight = 0.05


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

def calculate_probabilities(form_data):
    # Access the selected situations from the form data
    selected_situations = request.form.getlist('situations')
    situations = ["4v5 PK", "5v4 PP", "5v5", "5v5 Score & VA", "Even Strength", "All_Sit"]
    team1_stats = {}
    team2_stats = {}

    # Get the last 5 games win-loss records for both teams
    team1_last5 = form_data.get('team1_last5', "")
    team2_last5 = form_data.get('team2_last5', "")

    # Check if either team is playing a back-to-back game
    team1_back2back = request.form.get('team1_back2back') == 'Yes'
    team2_back2back = request.form.get('team2_back2back') == 'Yes'

    # Create empty dictionaries as placeholders for missing arguments
    team_last_5_games = {}
    home_team_back_2_back = {}

    # Add logic to populate the missing arguments
    if team1_last5:
        team_last_5_games['Team 1'] = {"W": int(team1_last5.split("-")[0]), "L": int(team1_last5.split("-")[1])}
    if team2_last5:
        team_last_5_games['Team 2'] = {"W": int(team2_last5.split("-")[0]), "L": int(team2_last5.split("-")[1])}
    home_team_back_2_back['Team 1'] = team1_back2back
    home_team_back_2_back['Team 2'] = team2_back2back

    for situation in situations:
        team1_stats[situation] = {}
        team2_stats[situation] = {}
        for key in weights.keys():
            value1 = request.form.get(f"team1_{situation.replace(' ', '_')}_{key}", "0")
            value2 = request.form.get(f"team2_{situation.replace(' ', '_')}_{key}", "0")
            team1_stats[situation][key] = float(value1) if value1 != '' else 0
            team2_stats[situation][key] = float(value2) if value2 != '' else 0

    weighted_stats = {}
    implied_probs = {}
    combined_implied_probs = {}
    final_probs = {}

    for situation in selected_situations:
        weighted_stats[situation] = calculate_weighted_average({"Team 1": team1_stats[situation], "Team 2": team2_stats[situation]})
        implied_probs[situation] = calculate_implied_probabilities(weighted_stats[situation])
        implied_probs_df = pd.DataFrame(implied_probs[situation]).T
        combined_implied_probs[situation] = calculate_combined_implied_probabilities(implied_probs_df)
        final_probs[situation] = calculate_final_probabilities(combined_implied_probs[situation], team_last_5_games, home_team_back_2_back)

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



