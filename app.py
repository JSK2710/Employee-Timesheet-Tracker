import json
from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret_key"

# File paths
users_file = "users.json"
timesheets_file = "timesheets.json"

# Load user data
try:
    with open(users_file, "r") as f:
        user_data = json.load(f)
    employees = user_data["employees"]
    managers = user_data["managers"]
except FileNotFoundError:
    employees = {}
    managers = {}

# Load timesheets data
try:
    with open(timesheets_file, "r") as f:
        timesheets = json.load(f)
except FileNotFoundError:
    timesheets = {}


# Decorator for requiring login
def login_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            if "username" not in session or (role == "employee" and session["username"] not in employees) or (
                    role == "manager" and session["username"] not in managers):
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return decorated_function
    return wrapper


@app.route("/", methods=["GET", "POST"])
@login_required("employee")
def index():
    if request.method == "POST":
        date = request.form["date"]
        hours_worked = request.form["hours_worked"]
        if session["username"] not in timesheets:
            timesheets[session["username"]] = {}
        if date not in timesheets[session["username"]]:
            timesheets[session["username"]][date] = {"hours_worked": hours_worked, "rating": None}
            with open(timesheets_file, "w") as f:
                json.dump(timesheets, f)
            return redirect(url_for("index"))
        else:
            return "You cannot change the hours for an existing date."
    return render_template("index.html", timesheet=timesheets.get(session["username"], {}))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in employees and employees[username]["password"] == password:
            session["username"] = username
            return redirect(url_for("index"))
        elif username in managers and managers[username]["password"] == password:
            session["username"] = username
            return redirect(url_for("manager"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html", error="")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]
        manager = request.form.get("manager") if role == "employee" else None

        # Add user to the appropriate group
        if role == "employee":
            employees[username] = {"password": password, "manager": manager}
        elif role == "manager":
            managers[username] = {"password": password}

        # Save updated data to users.json
        with open(users_file, "w") as f:
            json.dump({"employees": employees, "managers": managers}, f)

        return redirect(url_for("login"))
    return render_template("register.html", managers=managers)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/manager", methods=["GET", "POST"])
@login_required("manager")
def manager():
    if request.method == "POST":
        employee = request.form["employee"]
        date = request.form["date"]
        rating = int(request.form["rating"])
        if date in timesheets.get(employee, {}):
            timesheets[employee][date]["rating"] = rating
            with open(timesheets_file, "w") as f:
                json.dump(timesheets, f)
            return redirect(url_for("manager"))
        else:
            return "No timesheet entry found for this date."
    return render_template("manager.html", timesheets=timesheets)


if __name__ == "__main__":
    app.run(debug=True)
