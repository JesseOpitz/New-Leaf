import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load master data once when the app starts
DATA_URL = "https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/master_data.xlsx"  # <-- update me
df = pd.read_excel(url)

# Normalize scores to be between 0-1 (optional, depending on your data)
for col in ['walk_score', 'cost_score', 'density_score', 'diversity_score', 'politics_score', 'wfh_score', 'emp_score']:
    master_df[col] = master_df[col] / 100  # assuming scores were 0-100

@app.route('/match', methods=['POST'])
def match():
    try:
        data = request.json
        user_answers = data.get('answers', [])  # should be a list
        city_count = int(data.get('city_count', 5))  # how many to return
        show_avoid = bool(data.get('show_avoid', False))  # show bottom cities?

        if len(user_answers) != 8:
            return jsonify({'error': 'Invalid number of answers provided.'}), 400

        # Map user answers to weights
        weights = {
            'walk_score': float(user_answers[4]),
            'cost_score': float(user_answers[3]),
            'density_score': float(user_answers[6]),
            'diversity_score': float(user_answers[2]),
            'politics_score': float(user_answers[7]),
            'wfh_score': float(user_answers[5]),
            'emp_score': float(user_answers[1]),
            'safety_score': float(user_answers[0])  # We'll handle safety differently (not present directly)
        }

        # Assume safety_score = 100 - (density_score + walk_score)/2 (or another method)
        # For now, ignore "safety" as we don't have crime data in your sheet.

        # Calculate total weighted score
        master_df['score'] = (
            master_df['walk_score'] * weights['walk_score'] +
            master_df['cost_score'] * weights['cost_score'] +
            master_df['density_score'] * weights['density_score'] +
            master_df['diversity_score'] * weights['diversity_score'] +
            master_df['politics_score'] * weights['politics_score'] +
            master_df['wfh_score'] * weights['wfh_score'] +
            master_df['emp_score'] * weights['emp_score']
        )

        if show_avoid:
            best = master_df.sort_values(by='score', ascending=False).head(city_count)
            worst = master_df.sort_values(by='score', ascending=True).head(city_count)

            return jsonify({
                'recommendations': best[['state', 'city', 'positive']].to_dict(orient='records'),
                'avoid': worst[['state', 'city', 'negative']].to_dict(orient='records')
            })
        else:
            best = master_df.sort_values(by='score', ascending=False).head(city_count)
            return jsonify({
                'recommendations': best[['state', 'city', 'positive']].to_dict(orient='records')
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
