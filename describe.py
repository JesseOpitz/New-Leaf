import os
import json
import openai
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Set OpenAI API key from environment
openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route('/describe', methods=['POST'])
def describe():
    content = request.get_json()
    user_input = content.get("description", "").strip()

    if not user_input:
        return jsonify({"error": "Description cannot be empty"}), 400

    prompt = f"""
User provided this city preference description:
\"\"\"{user_input}\"\"\"

1. Based on this, rate the following categories from 0 (not mentioned) to 8 (very important):
- Safety
- Employment
- Diversity
- Affordability
- Walkability
- Remote Work
- Density (0=rural, 4=urban)
- Politics (0=very conservative, 8=very liberal)

2. Then write a friendly 1-2 sentence summary of what kind of place the user is looking for.

If the description is too vague to rate, say: "insufficient detail".

Return only a JSON object like:
{{
  "scores": [int, int, int, int, int, int, int, int], 
  "summary": "..."
}}
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw_output = response.choices[0].message.content.strip()

        # Attempt to parse JSON safely
        result = json.loads(raw_output)

        if result.get("summary", "").lower().startswith("insufficient"):
            return jsonify({
                "error": "Your description didn't include enough detail to generate matches. Try mentioning preferences like safety, affordability, diversity, etc."
            }), 400

        if not isinstance(result.get("scores"), list) or len(result["scores"]) != 8:
            return jsonify({"error": "AI response was incomplete. Please rephrase your description."}), 400

        return jsonify({
            "scores": result["scores"],
            "summary": result["summary"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
