from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load your updated master data
url = "https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/masterfile.xlsx"
data = pd.read_excel(url)

# Ensure required columns are present
required_columns = [
    'state', 'city', 'county',
    'walk_rank', 'cost_rank', 'density_rank', 'div_rank',
    'pol_rank', 'wfh_rank', 'crime_rank', 'emp_rank',
    'positive', 'negative', 'Wikipedia_URL'
]
assert all(col in data.columns for col in required_columns), "Missing columns in Master Data File!"

# Set max rank for normalization
max_rank = max(
    data['walk_rank'].max(),
    data['cost_rank'].max(),
    data['density_rank'].max(),
    data['div_rank'].max(),
    data['pol_rank'].max(),
    data['wfh_rank'].max(),
    data['crime_rank'].max(),
    data['emp_rank'].max()
)

@app.route('/', methods=['GET'])
def home():
    return "New Leaf API is Running!"

@app.route('/match', methods=['POST'])
def match():
    content = request.get_json()

    if not content or 'answers' not in content:
        return jsonify({"error": "No answers provided"}), 400

    try:
        answers = content['answers']
        safety = int(answers[0])
        employment = int(answers[1])
        diversity = int(answers[2])
        affordability = int(answers[3])
        walkability = int(answers[4])
        remote_work = int(answers[5])
        density_preference = int(answers[6])
        politics_preference = int(answers[7])  # 0 (conservative) to 8 (liberal)
        city_count = int(answers[8])
        show_avoid = answers[9]

        # Normalize user political preference to [-1, 1]
        normalized_user_pref = (politics_preference - 4) / 4

        scores = []

        for _, row in data.iterrows():
            score = 0

            # Category scores (lower rank is better)
            score += safety * (max_rank - row['crime_rank'])
            score += employment * (max_rank - row['emp_rank'])
            score += diversity * (max_rank - row['div_rank'])
            score += affordability * (max_rank - row['cost_rank'])
            score += walkability * (max_rank - row['walk_rank'])
            score += remote_work * (max_rank - row['wfh_rank'])

            # Density: score based on distance from user preference
            density_difference = abs(density_preference - row['density_rank'])
            score += max_rank - density_difference

            # Politics: normalize city political leaning to [-1, 1]
            normalized_city_pol = (max_rank - row['pol_rank']) / (max_rank - 1)  # [0,1]
            normalized_city_pol = (normalized_city_pol - 0.5) * 2  # [-1,1]

            # Closer match = higher score
            pol_score = (1 - abs(normalized_user_pref - normalized_city_pol)) * 100
            score += pol_score

            scores.append({
                "state": str(row['state']),
                "city": str(row['city']),
                "score": float(score),
                "positive": str(row['positive']),
                "negative": str(row['negative']),
                "Wikipedia_URL": str(row['Wikipedia_URL']) if pd.notna(row['Wikipedia_URL']) else ""
            })

        # Sort cities by score descending
        scores = sorted(scores, key=lambda x: x['score'], reverse=True)

        good_matches = scores[:city_count]
        bad_matches = scores[-city_count:] if show_avoid else []

        return jsonify({"good_matches": good_matches, "bad_matches": bad_matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
