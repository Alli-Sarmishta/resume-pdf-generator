from flask import Flask, request, jsonify
from generate_resume import generate_resume_pdf

app = Flask(__name__)

@app.route("/generate_resume", methods=["POST"])
def handle_resume_generation():
    try:
        data = request.json
        result = generate_resume_pdf(data)
        if result:
            return jsonify(result), 200
        else:
            return jsonify({"error": "PDF generation failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
