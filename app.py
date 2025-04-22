from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load your updated master data
url = "https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/masterfile.xlsx"
data = pd.read_excel(url)

# Normalize columns to ensure all required fields exist
required_columns = [
    'state', 'city', 'county',
    'walk_rank', 'cost_rank', 'density_rank', 'div_rank',
    'pol_rank', 'wfh_rank', 'crime_rank', 'emp_rank',
    'positive', 'negative'
]
assert all(col in data.columns for col in required_columns), "Missing columns in Master Data File!"

# Set max rank for normalization (highest possible rank)
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

    answers = content['answers']

    try:
        safety = int(answers[0])
        employment = int(answers[1])
        diversity = int(answers[2])
        affordability = int(answers[3])
        walkability = int(answers[4])
        remote_work = int(answers[5])
        density_preference = int(answers[6])
        politics_preference = int(answers[7])
        city_count = int(answers[8])
        show_avoid = answers[9]

        scores = []

        # politics multipliers as per your new formula
        politics_multipliers = [9, 7, 5, 3, 1, 3, 5, 7, 9]

        for _, row in data.iterrows():
            score = 0

            # Score regular categories (reversed: lower rank = better)
            score += safety * (max_rank - row['crime_rank'])
            score += employment * (max_rank - row['emp_rank'])
            score += diversity * (max_rank - row['div_rank'])
            score += affordability * (max_rank - row['cost_rank'])
            score += walkability * (max_rank - row['walk_rank'])
            score += remote_work * (max_rank - row['wfh_rank'])

            # Score density (direct match: lower distance is better)
            density_difference = abs(density_preference - row['density_rank'])
            density_score = max(0, max_rank - density_difference)
            score += density_score

            # Score politics using custom curve
            if politics_preference <= 4:
                pol_score = (max_rank - row['pol_rank']) * politics_multipliers[politics_preference]
            else:
                pol_score = row['pol_rank'] * politics_multipliers[politics_preference]
            score += pol_score

            scores.append({
                "state": str(row['state']),
                "city": str(row['city']),
                "score": float(score),
                "positive": str(row['positive']),
                "negative": str(row['negative'])
})

        # Sort by score descending
        scores = sorted(scores, key=lambda x: x['score'], reverse=True)

        good_matches = scores[:city_count]
        bad_matches = scores[-city_count:] if show_avoid else []

        return jsonify({"good_matches": good_matches, "bad_matches": bad_matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
