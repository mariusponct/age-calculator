import os
import calendar
from datetime import date, datetime
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)


def calculate_age(birth: date, today: date):
    """Return a dict with the age broken down several ways."""
    # --- Years / months / days breakdown ---
    years = today.year - birth.year
    months = today.month - birth.month
    days = today.day - birth.day

    if days < 0:
        months -= 1
        # borrow days from the previous month
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12

    # --- Totals ---
    delta = today - birth
    total_days = delta.days
    total_weeks = total_days // 7
    total_hours = total_days * 24
    total_months = years * 12 + months

    # --- Next birthday countdown ---
    next_bday_year = today.year
    try:
        next_bday = birth.replace(year=next_bday_year)
    except ValueError:  # Feb 29 on a non-leap year
        next_bday = date(next_bday_year, 3, 1)
    if next_bday < today:
        next_bday_year += 1
        try:
            next_bday = birth.replace(year=next_bday_year)
        except ValueError:
            next_bday = date(next_bday_year, 3, 1)
    days_to_bday = (next_bday - today).days

    return {
        "years": years,
        "months": months,
        "days": days,
        "total_months": total_months,
        "total_weeks": total_weeks,
        "total_days": total_days,
        "total_hours": total_hours,
        "weekday_born": birth.strftime("%A"),
        "days_to_birthday": days_to_bday,
        "turning": years + 1,
    }


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Age Calculator</title>
  <style>
    :root { color-scheme: light dark; }
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      margin: 0; min-height: 100vh; display: grid; place-items: center;
      padding: 1.5rem;
      background: linear-gradient(135deg, #475569, #94a3b8); color: #fff;
    }
    .card {
      background: rgba(255,255,255,0.12); backdrop-filter: blur(10px);
      padding: 2.5rem; border-radius: 20px; width: 100%; max-width: 540px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.35);
    }
    h1 { margin: 0 0 .3rem; font-size: 1.8rem; }
    p.sub { margin: 0 0 1.8rem; opacity: .8; }
    label { display: block; margin-bottom: .4rem; font-weight: 600; }
    .controls { display: flex; gap: .6rem; flex-wrap: wrap; }
    input[type=date] {
      flex: 1 1 200px; padding: .7rem .9rem; border: none; border-radius: 10px;
      font-size: 1rem; color: #1f2937; background: #fff; color-scheme: light;
    }
    button {
      padding: .7rem 1.5rem; border: none; border-radius: 10px;
      background: #fff; color: #334155; font-weight: 700; font-size: 1rem;
      cursor: pointer;
    }
    button:hover { background: #e2e8f0; }
    .hero {
      text-align: center; margin: 2rem 0 1.5rem;
      display: none;
    }
    .hero .big { font-size: 3.5rem; font-weight: 800; line-height: 1; }
    .hero .label { opacity: .85; margin-top: .4rem; }
    .grid {
      display: grid; grid-template-columns: repeat(2, 1fr); gap: .8rem;
      display: none;
    }
    .stat {
      background: rgba(0,0,0,0.5); border-radius: 12px; padding: 1rem;
      text-align: center;
    }
    .stat .num { font-size: 1.5rem; font-weight: 700; }
    .stat .cap { opacity: .75; font-size: .85rem; margin-top: .2rem; }
    .bday { margin-top: 1.2rem; text-align: center; opacity: .9;
            display: none; }
    .error { color: #ffe4e6; margin-top: 1rem; display: none;
             background: rgba(0,0,0,0.25); padding: .7rem; border-radius: 10px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🎂 Age Calculator TEST</h1>
    <p class="sub">Pick your birth date.</p>

    <label for="dob">Date of birth</label>
    <div class="controls">
      <input type="date" id="dob" max="">
      <button onclick="calc()">Calculate</button>
    </div>

    <div class="error" id="error"></div>

    <div class="hero" id="hero">
      <div class="big"><span id="y">0</span></div>
      <div class="label">
        years, <span id="m">0</span> months, <span id="d">0</span> days
      </div>
    </div>

    <div class="grid" id="grid">
      <div class="stat"><div class="num" id="tm">0</div><div class="cap">months</div></div>
      <div class="stat"><div class="num" id="tw">0</div><div class="cap">weeks</div></div>
      <div class="stat"><div class="num" id="td">0</div><div class="cap">days</div></div>
      <div class="stat"><div class="num" id="th">0</div><div class="cap">hours</div></div>
    </div>

    <div class="bday" id="bday"></div>
  </div>

  <script>
    // Don't allow future dates in the picker.
    document.getElementById("dob").max = new Date().toISOString().split("T")[0];

    async function calc() {
      const dob = document.getElementById("dob").value;
      const err = document.getElementById("error");
      if (!dob) {
        showError("Please pick a date first.");
        return;
      }
      try {
        const res = await fetch("/api/age", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dob })
        });
        const data = await res.json();
        if (!res.ok) { showError(data.error || "Something went wrong."); return; }

        err.style.display = "none";
        document.getElementById("y").textContent = data.years;
        document.getElementById("m").textContent = data.months;
        document.getElementById("d").textContent = data.days;
        document.getElementById("tm").textContent = data.total_months.toLocaleString();
        document.getElementById("tw").textContent = data.total_weeks.toLocaleString();
        document.getElementById("td").textContent = data.total_days.toLocaleString();
        document.getElementById("th").textContent = data.total_hours.toLocaleString();

        const b = document.getElementById("bday");
        if (data.days_to_birthday === 0) {
          b.textContent = "🎉 Happy birthday! It's today!";
        } else {
          b.textContent = `You were born on a ${data.weekday_born}. ` +
            `${data.days_to_birthday} day(s) until you turn ${data.turning}.`;
        }

        document.getElementById("hero").style.display = "block";
        document.getElementById("grid").style.display = "grid";
        b.style.display = "block";
      } catch (e) {
        showError("Could not reach the server.");
      }
    }

    function showError(msg) {
      const err = document.getElementById("error");
      err.textContent = msg;
      err.style.display = "block";
      document.getElementById("hero").style.display = "none";
      document.getElementById("grid").style.display = "none";
      document.getElementById("bday").style.display = "none";
    }

    // Allow Enter to trigger calculation.
    document.getElementById("dob").addEventListener("keydown", e => {
      if (e.key === "Enter") calc();
    });
  </script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/age", methods=["POST"])
def api_age():
    data = request.get_json(silent=True) or {}
    dob_str = data.get("dob", "")
    try:
        birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(error="Invalid date format."), 400

    today = date.today()
    if birth > today:
        return jsonify(error="Birth date can't be in the future."), 400

    return jsonify(calculate_age(birth, today))


# Health endpoint — handy if you ever do deploy this.
@app.route("/health")
def health():
    return jsonify(status="ok"), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)