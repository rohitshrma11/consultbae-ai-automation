from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "consultbae.db")


@app.route("/check-duplicate", methods=["POST"])
def check_duplicate():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    city = data.get("city")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    # Strong match: email or phone
    cursor.execute(
        """
        SELECT person_id, name, email, phone, city, sources
        FROM people
        WHERE
            (? IS NOT NULL AND email = ?)
            OR
            (? IS NOT NULL AND phone = ?)
        LIMIT 1
        """,
        (email, email, phone, phone)
    )

    person = cursor.fetchone()

    match_reason = None

    if person:

        if email and person["email"] == email:
            match_reason = "email"

        elif phone and person["phone"] == phone:
            match_reason = "phone"

    else:

        # Fallback: name + city
        cursor.execute(
            """
            SELECT person_id, name, email, phone, city, sources
            FROM people
            WHERE name = ? AND city = ?
            LIMIT 1
            """,
            (name, city)
        )

        person = cursor.fetchone()

        if person:
            match_reason = "name_city"

    conn.close()

    if person:

        return jsonify({
            "duplicate": True,
            "match_reason": match_reason,
            "person_id": person["person_id"],
            "matched_name": person["name"],
            "email": person["email"],
            "phone": person["phone"],
            "city": person["city"],
            "sources": person["sources"]
        })

    return jsonify({
        "duplicate": False,
        "match_reason": None,
        "message": "New candidate"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )