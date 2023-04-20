from flask import Flask, render_template, request
import re
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def calculate_probabilities():
    data = request.form
    team_stats = {
        'Team 1_Away': {
            'CF%': float(data['Team1_CF']),
            'FF%': float(data['Team1_FF']),
            'xGF%': float(data['Team1_xGF']),
            'HDCF%': float(data['Team1_HDCF']),
            'HDSF%': float(data['Team1_HDSF']),
            'PDO': float(data['Team1_PDO']),
        },
        'Team 2_Home': {
            'CF%': float(data['Team2_CF']),
            'FF%': float(data['Team2_FF']),
            'xGF%': float(data['Team2_xGF']),
            'HDCF%': float(data['Team2_HDCF']),
            'HDSF%': float(data['Team2_HDSF']),
            'PDO': float(data['Team2_PDO']),
        }
    }

    # Calculate the implied probabilities for All_Situations
    final_probs = {team: sum(team_stats[team].values()) / 6 for team in team_stats.keys()}
    sum_probs = sum(final_probs.values())
    norm_probs = {team: final_probs[team] / sum_probs for team in final_probs.keys()}
    print("Final Probs:", norm_probs)

    team1_recent_game_wins = int(data['Team1_RecentGame'])
    team2_recent_game_wins = int(data['Team2_RecentGame'])

    weighted_probs = {
    team: (
        0.7 * norm_probs[team] +
        0.2 * (team1_recent_game_wins / 5 if team.endswith("Away") else team2_recent_game_wins / 5) +
        0.05 * (0.45 if team.endswith("Away") else 0.55) +
        (lambda t_num: 0.05 * (0 if data[f'Team{t_num}_Back2Back'] == "No" else -0.25))(re.findall(r"(\d+)", team)[0])
    )
    for team in team_stats.keys()
}

    # Normalize the weighted probabilities
    sum_weighted_probs = sum(weighted_probs.values())
    final_probs = {team: (weighted_probs[team] / sum_weighted_probs) * 100 for team in weighted_probs.keys()}

    return render_template('index.html', final_probs=final_probs)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))








