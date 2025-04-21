from flask import Flask, request, jsonify
import pandas as pd

app = Flask(__name__)

# Load your updated master data
url = "https://raw.githubusercontent.com/your-username/your-repo-name/main/Master%20Data%20File.xlsx"
data = pd.read_excel(url)

# Normalize columns to ensure all required fields exist
required_columns = ['state', 'city', 'walk_score', 'cost_score', 'density_score', 'diversity_score', 'politics_score', 'wfh_score', 'emp_score', 'positive', 'negative']
assert all(col in data.columns for col in required_columns), "Missing columns in Master Data File!"

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
        density_importance = int(answers[7])
        politics_preference = int(answers[8])
        politics_importance = int(answers[9])
        city_count = int(answers[10])
        show_avoid = answers[11]

        scores = []

        for _, row in data.iterrows():
            score = 0

            # Regular categories (0-100 scales)
            score += safety * (row['walk_score'] / 100)  # Walk Score proxy for safety
            score += employment * (row['emp_score'] / 100)
            score += diversity * (row['diversity_score'] / 100)
            score += affordability * (row['cost_score'] / 100)
            score += walkability * (row['walk_score'] / 100)
            score += remote_work * (row['wfh_score'] / 100)

            # Density (1 to 5 scale)
            density_difference = abs(density_preference - row['density_score'])
            density_points = max(0, 100 - (density_difference * 20))
            score += density_importance * (density_points / 100)

            # Politics (1 to 5 scaled manually, assuming you scaled already)
            politics_mapped_user = politics_preference  # from 0-8 to 1-5
            politics_mapped_row = row['politics_score']  # Already 1-5
            politics_difference = abs(politics_mapped_user - politics_mapped_row)
            politics_points = max(0, 100 - (politics_difference * 20))
            score += politics_importance * (politics_points / 100)

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
