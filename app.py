from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load your updated master data
url = "https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/master_data.xlsx"
data = pd.read_excel(url)

# Normalize columns to ensure all required fields exist
required_columns = ['state', 'city', 'walk_score', 'cost_score', 'density_score', 'diversity_score', 'politics_score', 'wfh_score', 'emp_score', 'positive', 'negative']
assert all(col in data.columns for col in required_columns), "Missing columns in Master Data File!"

# Min-max normalization (for scoring)
walk_min, walk_max = data['walk_score'].min(), data['walk_score'].max()
cost_min, cost_max = data['cost_score'].min(), data['cost_score'].max()
diversity_min, diversity_max = data['diversity_score'].min(), data['diversity_score'].max()
politics_min, politics_max = data['politics_score'].min(), data['politics_score'].max()
wfh_min, wfh_max = data['wfh_score'].min(), data['wfh_score'].max()
emp_min, emp_max = data['emp_score'].min(), data['emp_score'].max()  # LOWER is better

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

        for _, row in data.iterrows():
            score = 0

            # Normalize features
            walk_norm = (row['walk_score'] - walk_min) / (walk_max - walk_min)
            cost_norm = (row['cost_score'] - cost_min) / (cost_max - cost_min)
            diversity_norm = (row['diversity_score'] - diversity_min) / (diversity_max - diversity_min)
            politics_norm = (row['politics_score'] - politics_min) / (politics_max - politics_min)
            wfh_norm = (row['wfh_score'] - wfh_min) / (wfh_max - wfh_min)
            emp_norm = 1 - (row['emp_score'] - emp_min) / (emp_max - emp_min)  # REVERSED

            # Regular scoring (normalized 0-1)
            score += safety * walk_norm
            score += employment * emp_norm
            score += diversity * diversity_norm
            score += affordability * cost_norm
            score += walkability * walk_norm
            score += remote_work * wfh_norm

            # Density (difference based)
            density_difference = abs(density_preference - row['density_score'])
            density_points = max(0, 100 - (density_difference * 20))
            score += (density_points / 100)

            # Politics (now like regular categories!)
            politics_difference = abs(politics_preference - row['politics_score'])
            politics_points = max(0, 100 - (politics_difference * 20))
            score += (politics_points / 100)

            scores.append({
                "state": row['state'],
                "city": row['city'],
                "score": score,
                "positive": row['positive'],
                "negative": row['negative']
            })

        # Sort scores highest first
        scores = sorted(scores, key=lambda x: x['score'], reverse=True)

        good_matches = scores[:city_count]
        bad_matches = scores[-city_count:] if show_avoid else []

        return jsonify({"good_matches": good_matches, "bad_matches": bad_matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
