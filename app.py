import re
import hashlib
import datetime
import time
import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secure_university_secret_key"

users = {}
failed_attempts = {}
blocked_users = set()
activity_logs = []

LOG_FILE = "logs/login_activity.log"
REPORT_FILE = "static/suspicious_report.png"

os.makedirs("logs", exist_ok=True)
os.makedirs("static", exist_ok=True)


# Hash password using SHA-256
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Validate university email format
def validate_username(username):
    pattern = r"^[a-zA-Z0-9_.]+@university\.edu$"
    return re.match(pattern, username) is not None


# Validate strong password
def validate_password(password):
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"[0-9]", password)
        and re.search(r"[@#$%^&+=!]", password)
    )


# Write activity logs into external file
def write_log(username, activity):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"{timestamp} | {username} | {activity}"
    activity_logs.append(log)

    with open(LOG_FILE, "a") as file:
        file.write(log + "\n")


# Generate suspicious activity report with graph
def generate_report():
    suspicious_count = {}

    for log in activity_logs:
        parts = log.split("|")
        username = parts[1].strip()
        activity = parts[2].strip()

        if activity in [
            "LOGIN_FAILED",
            "ACCOUNT_BLOCKED",
            "BLOCKED_LOGIN_ATTEMPT",
            "UNKNOWN_USER_ATTEMPT",
        ]:
            suspicious_count[username] = suspicious_count.get(username, 0) + 1

    if suspicious_count:
        plt.figure(figsize=(8, 5))
        plt.bar(suspicious_count.keys(), suspicious_count.values())
        plt.xlabel("Username")
        plt.ylabel("Suspicious Activity Count")
        plt.title("Suspicious Login Activity Report")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(REPORT_FILE)
        plt.close()

    return suspicious_count


@app.route("/")
def home():
    report = generate_report()
    return render_template("index.html", report=report, users=users, blocked_users=blocked_users)


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"]
    password = request.form["password"]

    if not validate_username(username):
        return redirect(url_for("home", msg="Invalid username format. Use name@university.edu"))

    if not validate_password(password):
        return redirect(url_for("home", msg="Weak password. Use uppercase, lowercase, digit, special character and minimum 8 characters."))

    users[username] = hash_password(password)
    failed_attempts[username] = 0
    write_log(username, "USER_REGISTERED")

    return redirect(url_for("home", msg="User registered successfully."))


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username in blocked_users:
        write_log(username, "BLOCKED_LOGIN_ATTEMPT")
        return redirect(url_for("home", msg="Account is blocked."))

    if username not in users:
        write_log(username, "UNKNOWN_USER_ATTEMPT")
        return redirect(url_for("home", msg="User not found."))

    if users[username] == hash_password(password):
        failed_attempts[username] = 0
        session["username"] = username
        session["login_time"] = time.time()
        write_log(username, "LOGIN_SUCCESS")
        return redirect(url_for("dashboard"))

    failed_attempts[username] += 1
    write_log(username, "LOGIN_FAILED")

    if failed_attempts[username] >= 3:
        blocked_users.add(username)
        write_log(username, "ACCOUNT_BLOCKED")
        return redirect(url_for("home", msg="Account blocked after 3 failed attempts."))

    return redirect(url_for("home", msg="Invalid password."))


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("home", msg="Please login first."))

    timeout = 15

    if time.time() - session["login_time"] > timeout:
        write_log(session["username"], "SESSION_TIMEOUT")
        session.clear()
        return redirect(url_for("home", msg="Session timeout."))

    write_log(session["username"], "RESOURCE_ACCESSED")
    return f"""
    <h1>Welcome, {session["username"]}</h1>
    <p>Student resource accessed successfully.</p>
    <a href='/logout'>Logout</a>
    """


@app.route("/logout")
def logout():
    if "username" in session:
        write_log(session["username"], "LOGOUT")
    session.clear()
    return redirect(url_for("home", msg="Logged out successfully."))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
