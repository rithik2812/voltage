from flask import Flask, render_template, request
import cmath

app = Flask(__name__)

def calculate_voltages(V_s, total_length, z_per_meter, load_points):
    # Sort loads by distance (descending) and include source
    load_points = sorted(load_points, key=lambda x: x[0], reverse=True)
    load_points.append((0, 0 + 0j))  # Add source as reference point

    voltages = {}
    I_total = 0 + 0j  # Total current downstream of the current segment
    V = V_s  # Voltage at the source

    for i in range(len(load_points) - 1):
        d_current, S_current = load_points[i]
        d_next, S_next = load_points[i + 1]

        segment_length = d_current - d_next  # Distance between consecutive loads
        Z_segment = z_per_meter * segment_length

        # Update total current with the current load
        I_load = (S_current.conjugate() / V) if abs(V) > 1e-6 else 0
        I_total += I_load

        # Calculate voltage drop and update upstream voltage
        V_drop = I_total * Z_segment
        V = V - V_drop

        # Store voltage at the current load point
        voltages[d_current] = V

    return voltages

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return empty response (no content)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            V_mag = float(request.form["V_mag"])
            V_angle = float(request.form["V_angle"])
            V_s = cmath.rect(V_mag, cmath.pi * V_angle / 180)

            total_length = float(request.form["total_length"])
            R = float(request.form["R"])
            X = float(request.form["X"])
            z_per_meter = complex(R, X)

            distances = request.form.getlist("distance[]")
            Ps = request.form.getlist("P[]")
            Qs = request.form.getlist("Q[]")

            load_points = []
            for d, p, q in zip(distances, Ps, Qs):
                if d and p and q:
                    load_points.append((float(d), complex(float(p), float(q))))

            voltages = calculate_voltages(V_s, total_length, z_per_meter, load_points)

            formatted_results = [
                {
                    "distance": dist,
                    "magnitude": round(abs(v), 2),
                    "angle": round(cmath.phase(v) * 180 / cmath.pi, 2)
                }
                for dist, v in sorted(voltages.items())
            ]

            return render_template("index.html", result=formatted_results)

        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")
if __name__ == "__main__":
    app.run(debug=True)
