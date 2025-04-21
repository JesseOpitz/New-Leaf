# app.py
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)

# Load your dataset once at startup
data_url = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/Master%20Data%20File.xlsx"  # <-- replace this
data = pd.read_excel(data_url)

@app.route("/", methods=["GET"])
def home():
    return "New Leaf API is live!"

@app.route("/match", methods=["POST"])
def match_cities():
    try:
        req = request.get_json()
        answers = req.get("answers", [])

        if not answers or len(answers) < 10:
            return jsonify({"error": "Invalid input"}), 400

        # Extract user's preferences
        weights = {
            "walk_score": float(answers[0]),
            "emp_score": float(answers[1]),
            "diversity_score": float(answers[2]),
            "cost_score": float(answers[3]),
            "walk_score_2": float(answers[4]),  # for walkability again
            "wfh_score": float(answers[5]),
            "density_score": float(answers[6]),
            "density_importance": float(answers[7]),
            "politics_score": float(answers[8]),
            "politics_importance": float(answers[9])
        }

        city_count = int(answers[10]) if len(answers) > 10 else 5
        show_avoid = bool(answers[11]) if len(answers) > 11 else False

        # Normalize importance values (make total weighting sum to 1)
        importance = np.array([
            weights["walk_score"],
            weights["emp_score"],
            weights["diversity_score"],
            weights["cost_score"],
            weights["walk_score_2"],
            weights["wfh_score"],
            weights["density_importance"],
            weights["politics_importance"]
        ])
        importance_sum = importance.sum()
        if importance_sum == 0:
            importance_sum = 1  # avoid division by zero
        normalized_importance = importance / importance_sum

        # Calculate weighted scores
        scores = (
            (data["walk_score"] * normalized_importance[0]) +
            (data["emp_score"] * normalized_importance[1]) +
            (data["diversity_score"] * normalized_importance[2]) +
            (data["cost_score"] * normalized_importance[3]) +
            (data["walk_score"] * normalized_importance[4]) +
            (data["wfh_score"] * normalized_importance[5]) +
            (100 - abs(data["density_score"] - weights["density_score"]*25)) * normalized_importance[6] +
            (100 - abs(data["politics_score"] - weights["politics_score"]*12.5)) * normalized_importance[7]
        )

        data["final_score"] = scores

        # Get good matches (top scoring)
        good_matches = data.sort_values(by="final_score", ascending=False).head(city_count)
        good_matches_list = good_matches[["city", "state", "positive"]].to_dict(orient="records")

        # Get avoid matches (lowest scoring)
        bad_matches_list = []
        if show_avoid:
            bad_matches = data.sort_values(by="final_score", ascending=True).head(city_count)
            bad_matches_list = bad_matches[["city", "state", "negative"]].to_dict(orient="records")

        return jsonify({
            "good_matches": good_matches_list,
            "bad_matches": bad_matches_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
