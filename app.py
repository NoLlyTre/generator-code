import math
import random
import secrets
from io import StringIO
from typing import Any
from flask import Flask, request, jsonify, session, Response, render_template


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secrets.token_urlsafe(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        PERMANENT_SESSION_LIFETIME=3600 * 6,
    )

    CHARSETS = {
        "lowercase": "abcdefghijklmnopqrstuvwxyz",
        "uppercase": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "numbers": "0123456789",
        "symbols": "!@#$%^&*()-_=+[]{};:,.<>/?|~",
    }

    def build_charset(uppercase, lowercase, numbers, symbols):
        parts = []
        if lowercase:
            parts.append(CHARSETS["lowercase"])
        if uppercase:
            parts.append(CHARSETS["uppercase"])
        if numbers:
            parts.append(CHARSETS["numbers"])
        if symbols:
            parts.append(CHARSETS["symbols"])
        return "".join(parts)

    def calculate_bits(charset_size, length):
        return round(length * math.log2(charset_size), 1) if charset_size and length else 0.0

    def score_percent_from_bits(bits):
        if bits <= 0:
            return 0
        return min(100, round(bits / 64 * 100))

    def generate_password(length, uppercase, lowercase, numbers, symbols):
        charset = build_charset(uppercase, lowercase, numbers, symbols)
        if not charset:
            raise ValueError("no_charsets")

        required = []
        if lowercase:
            required.append(secrets.choice(CHARSETS["lowercase"]))
        if uppercase:
            required.append(secrets.choice(CHARSETS["uppercase"]))
        if numbers:
            required.append(secrets.choice(CHARSETS["numbers"]))
        if symbols:
            required.append(secrets.choice(CHARSETS["symbols"]))

        required = required[:length]
        remaining = length - len(required)
        pwd_chars = required + [secrets.choice(charset) for _ in range(remaining)]
        random.SystemRandom().shuffle(pwd_chars)
        return "".join(pwd_chars)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.post("/generate")
    def generate():
        data = request.get_json(silent=True) or request.form.to_dict()
        length = int(data.get("length", 16))
        count = int(data.get("count", 5))
        length = max(4, min(256, length))
        count = max(1, min(100, count))

        flags = {
            "uppercase": str(data.get("uppercase", "true")).lower() in {"1", "true", "yes", "on"},
            "lowercase": str(data.get("lowercase", "true")).lower() in {"1", "true", "yes", "on"},
            "numbers": str(data.get("numbers", "true")).lower() in {"1", "true", "yes", "on"},
            "symbols": str(data.get("symbols", "false")).lower() in {"1", "true", "yes", "on"},
        }

        try:
            charset = build_charset(**flags)
            if not charset:
                raise ValueError("no_charsets")

            charset_size = len(set(charset))
            passwords = []

            for _ in range(count):
                pwd = generate_password(length, **flags)
                bits = calculate_bits(charset_size, length)
                score = score_percent_from_bits(bits)
                passwords.append({"password": pwd, "bits": bits, "score_percent": score})

        except ValueError as e:
            if str(e) == "no_charsets":
                return jsonify(error="Выберите хотя бы один тип символов"), 400
            raise

        session.permanent = True
        hist = session.get("history", [])
        hist.extend(passwords)
        session["history"] = hist[-100:]

        return jsonify({"passwords": passwords})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5050)
