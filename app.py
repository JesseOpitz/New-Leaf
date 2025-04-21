from flask import Flask, request, jsonify
import pandas as pd
import requests

app = Flask(__name__)

# URL to your master file on GitHub (replace with your real URL)
MASTER_FILE_URL = "https://raw.githubusercontent.com/JesseOpitz/New-Leaf/main/Master%20Data%20File.xlsx"

# Load the master data once when app starts
print("Loading master data...")
master_df = pd.read_excel(MASTER_FILE_URL)
print(f"Loaded {len(master_df)} cities.")

# Normalization helper (0-1 scaling)
def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

# Pre-normalize numerical columns
score_columns = ["walk_score", "cost_score", "density_score", "diversity_score", "politics_score", "wfh_score", "emp_score"]
for col in score_columns:
    master_df[col] = normalize(master_df[col])

@app.route('/')
def home():
    return "Backend is live."

@app.route('/match', methods=['POST'])
def match():
    data = request.json
    print("Received user answers:", data)

    try:
        user_importance = data.get('importance', {})
        num_results = int(data.get('num_results', 5))
        show_avoid = bool(data.get('show_avoid', False))

        # Calculate match score
        df = master_df.copy()
        df['match_score'] = 0

        for feature in score_columns:
            user_weight = user_importance.get(feature, 5)  # Default medium importance if missing
            df['match_score'] += df[feature] * user_weight

        # Sort and pick top matches
        top_matches = df.sort_values(by='match_score', ascending=False).head(num_results)

        result = {
            "matches": top_matches[["city", "state", "positive"]].to_dict(orient='records')
        }

        if show_avoid:
            bottom_matches = df.sort_values(by='match_score', ascending=True).head(num_results)
            result["avoid"] = bottom_matches[["city", "state", "negative"]].to_dict(orient='records')

        return jsonify(result)

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong during matching."}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
