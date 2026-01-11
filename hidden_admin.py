from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Simulated database
users = {
    "info@infinityxonesystems.com": {
        "password": generate_password_hash("success1234!!"),
        "role": "admin",
    }
}


@app.route("/admin/login", methods=["POST"])
def admin_login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = users.get(email)
    if user and check_password_hash(user["password"], password):
        if user["role"] == "admin":
            return jsonify({"message": "Welcome, Admin!", "status": "success"}), 200
        return (
            jsonify({"message": "Access denied. Not an admin.", "status": "error"}),
            403,
        )

    return jsonify({"message": "Invalid credentials.", "status": "error"}), 401


if __name__ == "__main__":
    app.run(debug=True)
