from flask import Flask, request, redirect, url_for, render_template_string, flash
from datetime import datetime
import os
import csv

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------
# SPECIAL PRODUCTS
# -----------------------
sun_special_products = [
    "admenta", "donamem", "lithosun", "zeptol cr", "zeptol",
    "delsia", "irovel", "octridE", "prazopress xl", "prolomet xl"
]

intas_special_products = [
    "amphotericin b", "epofit", "erypeg", "mycofit", "takfa", "terifrac"
]

def normalize_name(name: str) -> str:
    return ''.join(c for c in name.lower() if c.isalpha() or c.isspace()).strip()

def calculate_rate(company, product, sp, origin=None):
    company = company.lower().strip()
    product_norm = normalize_name(product)

    if company == "intas":
        if any(p in product_norm for p in intas_special_products):
            return sp / 1.20
        else:
            return sp / 1.24
    elif company == "sun":
        if any(p in product_norm for p in sun_special_products):
            return sp / 1.18
        else:
            return sp / 1.24
    elif company in ["cipla", "mankind", "astra zenica"]:
        return sp / 1.21
    elif company == "bhaskar":
        return sp / 1.31
    elif company == "lomus":
        return sp / 1.70
    else:
        if origin is None:
            origin = "Nepali"
        if origin.lower() == "nepali":
            return sp / 1.25
        else:
            return sp / 1.19

# -----------------------
# STORAGE
# -----------------------
def get_csv_file(month=None):
    if month is None:
        month = datetime.now().strftime("%B_%Y")
    return f"records_{month}.csv"

def save_record(data, month=None):
    filename = get_csv_file(month)
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Date", "Medicine", "Company", "Qty", "SP", "Rate", "Total", "Verified By", "Billed By"])
        writer.writerow(data)

def read_records(month=None):
    filename = get_csv_file(month)
    records = []
    if os.path.isfile(filename):
        with open(filename, newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            records = list(reader)
    return records

def write_records(records, month=None):
    """Overwrite CSV file with updated records"""
    filename = get_csv_file(month)
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Medicine", "Company", "Qty", "SP", "Rate", "Total", "Verified By", "Billed By"])
        writer.writerows(records)

def get_all_months():
    files = [f for f in os.listdir() if f.startswith("records_") and f.endswith(".csv")]
    months = [f.replace("records_","").replace(".csv","") for f in files]
    months.sort(reverse=True)
    return months

# -----------------------
# HTML TEMPLATE
# -----------------------
html = """
<!DOCTYPE html>
<html>
<head>
    <title>Riyan Pharmacy Billing</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
    <h2 class="text-center mb-4">Riyan Pharmacy Billing</h2>

    <!-- Billing Form -->
    <div class="card shadow-sm mb-4">
        <div class="card-body">
            <form method="POST" class="row g-3">
                <div class="col-md-4"><input type="text" name="medicine" class="form-control" placeholder="Medicine Name" required></div>
                <div class="col-md-3"><input type="text" name="company" class="form-control" placeholder="Company" required></div>
                <div class="col-md-2"><input type="number" name="qty" class="form-control" placeholder="Qty" required></div>
                <div class="col-md-2"><input type="number" step="0.01" name="sp" class="form-control" placeholder="SP" required></div>
                <div class="col-md-3"><input type="text" name="verified_by" class="form-control" placeholder="Verified By"></div>
                <div class="col-md-3"><input type="text" name="billed_by" class="form-control" placeholder="Billed By"></div>
                <div class="col-md-3">
                    <select name="origin" class="form-select">
                        <option value="Nepali">Nepali</option>
                        <option value="Indian">Indian</option>
                    </select>
                </div>
                <div class="col-12 text-end">
                    <button type="submit" class="btn btn-success mt-3">Add Record</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for category, msg in messages %}
          <div class="alert alert-{{category}}">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}

    <!-- Month Selector -->
    <form method="GET" class="mb-3">
        <label>Select Month:</label>
        <select name="month" class="form-select w-25 d-inline-block" onchange="this.form.submit()">
            {% for m in months %}
                <option value="{{m}}" {% if m == current_month %}selected{% endif %}>{{m}}</option>
            {% endfor %}
        </select>
    </form>

    <!-- Records Table -->
    <div class="card shadow-sm">
        <div class="card-body">
            <h4 class="mb-3">📋 Billing Records ({{current_month}})</h4>
            <div class="table-responsive">
                <table class="table table-striped table-hover">
                    <thead class="table-dark">
                        <tr>
                            <th>Date</th>
                            <th>Medicine</th>
                            <th>Company</th>
                            <th>Qty</th>
                            <th>SP</th>
                            <th>Rate</th>
                            <th>Total</th>
                            <th>Verified</th>
                            <th>Billed</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for r in records %}
                        <tr>
                            <td>{{ r[0] }}</td>
                            <td>{{ r[1] }}</td>
                            <td>{{ r[2] }}</td>
                            <td>{{ r[3] }}</td>
                            <td>{{ r[4] }}</td>
                            <td>{{ r[5] }}</td>
                            <td>{{ r[6] }}</td>
                            <td>{{ r[7] }}</td>
                            <td>{{ r[8] }}</td>
                            <td>
                                <form method="POST" action="/delete_single" style="display:inline-block;">
                                    <input type="hidden" name="row_index" value="{{ loop.index0 }}">
                                    <input type="password" name="password" class="form-control form-control-sm mb-1" placeholder="Password">
                                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                                </form>
                            </td>
                        </tr>
                        {% endfor %}
                        {% if records|length == 0 %}
                        <tr><td colspan="10" class="text-center text-muted">No records found</td></tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Delete All Records -->
    <form method="POST" action="/delete" class="mt-4">
        <input type="password" name="password" class="form-control w-25 d-inline-block" placeholder="Enter password to delete all">
        <button type="submit" class="btn btn-danger">Delete All Records</button>
    </form>

</div>
</body>
</html>
"""

# -----------------------
# ROUTES
# -----------------------
@app.route("/", methods=["GET", "POST"])
def billing():
    current_month = request.args.get("month") or datetime.now().strftime("%B_%Y")

    if request.method == "POST":
        medicine = request.form["medicine"]
        company = request.form["company"]
        qty = int(request.form["qty"])
        sp = float(request.form["sp"])
        verified_by = request.form["verified_by"]
        billed_by = request.form["billed_by"]
        origin = request.form.get("origin", "Nepali")

        rate = calculate_rate(company, medicine, sp, origin)
        total = round(rate * qty, 2)
        rate = round(rate, 2)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        save_record([date, medicine, company, qty, sp, rate, total, verified_by, billed_by])
        flash("Record saved successfully!", "success")
        return redirect(url_for("billing", month=current_month))

    months = get_all_months()
    records = read_records(current_month)
    return render_template_string(html, records=records, months=months, current_month=current_month)

@app.route("/delete", methods=["POST"])
def delete_records():
    password = request.form["password"]
    if password == "Lamine@10":
        for f in os.listdir():
            if f.startswith("records_") and f.endswith(".csv"):
                os.remove(f)
        flash("All records deleted successfully!", "danger")
    else:
        flash("Incorrect password!", "danger")
    return redirect(url_for("billing"))

@app.route("/delete_single", methods=["POST"])
def delete_single():
    password = request.form["password"]
    if password != "Lamine@10":
        flash("Incorrect password!", "danger")
        return redirect(url_for("billing"))

    row_index = int(request.form["row_index"])
    current_month = datetime.now().strftime("%B_%Y")
    records = read_records(current_month)
    if 0 <= row_index < len(records):
        del records[row_index]
        write_records(records, current_month)
        flash("Record deleted successfully!", "success")
    else:
        flash("Record not found!", "danger")
    return redirect(url_for("billing"))

# -----------------------
# HOST/PORT for Render
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
