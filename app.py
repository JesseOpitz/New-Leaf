from flask import Flask, request, jsonify
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load your master data file once when the app starts
url = 'https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/master_file.xlsx'
data = pd.read_excel(url)

# Simple helper to normalize scores
def normalize(val, min_val=0, max_val=8):
    return (float(val) - min_val) / (max_val - min_val)

@app.route('/', methods=['POST'])
def match_cities():
    try:
        content = request.get_json()
        answers = content.get('answers', [])

        # Separate the answers
        weights = {
            'safety': normalize(answers[0]),
            'employment': normalize(answers[1]),
            'diversity': normalize(answers[2]),
            'affordability': normalize(answers[3]),
            'walkability': normalize(answers[4]),
            'wfh': normalize(answers[5]),
            'density_pref': normalize(answers[6], 0, 4),
            'density_importance': normalize(answers[7]),
            'politics_pref': normalize(answers[8], 0, 8),
            'politics_importance': normalize(answers[9]),
        }
        show_top_n = int(answers[10])
        show_avoid = answers[11]

        # Calculate total score
        df = data.copy()
        df['total_score'] = (
            df['walk_score'] * weights['walkability'] +
            df['cost_score'] * weights['affordability'] +
            df['density_score'] * (1 - abs(df['density_score'] - weights['density_pref'])) * weights['density_importance'] +
            df['diversity_score'] * weights['diversity'] +
            df['politics_score'] * (1 - abs(df['politics_score'] - weights['politics_pref'])) * weights['politics_importance'] +
            df['wfh_score'] * weights['wfh'] +
            df['emp_score'] * weights['employment']
        )

        df_sorted = df.sort_values('total_score', ascending=False)

        good_matches = df_sorted.head(show_top_n)[['city', 'state', 'positive']].to_dict(orient='records')

        bad_matches = []
        if show_avoid:
            bad_matches = df_sorted.tail(show_top_n)[['city', 'state', 'negative']].to_dict(orient='records')

        return jsonify({
            "good_matches": good_matches,
            "bad_matches": bad_matches
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
