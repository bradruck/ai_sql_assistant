from flask import Flask, request, jsonify, send_from_directory
import openai
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load OpenAI Client
def create_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")

    try:
        client = openai.OpenAI(api_key=api_key, project="proj_yadk17XSGzr8n2a5jsF2VUvO")

        # Collect available models
        models = client.models.list()

        # Save OpenAI models list as json file
        with open('openai_model_list.json', 'w') as models_json:
            for model in models:
                models_json.write(str(model.id))
                models_json.write('\n')

    except openai.AuthenticationError:
        raise ValueError("Invalid OpenAI API key. Please check your OPENAI_API_KEY.")
    except openai.OpenAIError as e:
        raise RuntimeError(f"Failed to connect to OpenAI API: {e}")

    return client

# Initialize client once at startup
openai_client = create_openai_client()

# Serve frontend
@app.route("/", methods=["GET"])
def serve_frontend():
    return send_from_directory('.', 'tester_with_loading.html')

# Reload client manually if needed (optional feature)
@app.route("/reload-client", methods=["POST"])
def reload_openai_client():
    global openai_client
    try:
        openai_client = create_openai_client()
        return jsonify({"message": "OpenAI client reloaded successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Main generate SQL endpoint
@app.route("/generate", methods=["POST"])
def generate_sql():
    try:
        data = request.json
        question = data.get("question", "")

        if not question:
            return jsonify({"error": "Missing 'question' in request body"}), 400

        prompt = f"""
You are a SQL expert. Use the following schema:

Table: employees  
Columns: id, name, department, salary, date_joined  

### Convert the following question into a SQL query:  
{question}  

SQL:
        """

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that writes SQL queries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150
        )

        sql_text = response.choices[0].message.content.strip()
        return jsonify({"sql": sql_text})

    except openai.AuthenticationError:
        return jsonify({"error": "Invalid OpenAI API key. Check your credentials."}), 401
    except openai.RateLimitError:
        return jsonify({"error": "OpenAI API rate limit exceeded."}), 429
    except openai.OpenAIError as e:
        return jsonify({"error": f"OpenAI error: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
