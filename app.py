from flask import Flask, render_template, request
import cmath, math

app = Flask(__name__)

def calculate_voltages(V_s, total_length, z_per_meter, load_points):
    """
    (unchanged)
    """
    loads = sorted(load_points, key=lambda x: x[0])
    distances = [d for d, _ in loads]
    currents = [I for _, I in loads]
    cum_currents = [sum(currents[i:]) for i in range(len(currents))]

    voltages = {}
    V_prev = V_s
    for i, d in enumerate(distances):
        seg_len = d if i == 0 else d - distances[i-1]
        Z_seg = z_per_meter * seg_len
        I_down = cum_currents[i]
        V_here = V_prev - Z_seg * I_down
        voltages[d] = V_here
        V_prev = V_here

    return voltages

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # 1. Source voltage
            V_mag   = float(request.form["V_mag"])
            V_angle = float(request.form["V_angle"])
            V_s = cmath.rect(V_mag, math.radians(V_angle))

            # 2. Feeder parameters
            total_length = float(request.form["total_length"])
            R = float(request.form["R"])
            X = float(request.form["X"])
            z_per_meter = complex(R, X)

            # 3. Load inputs: distance, current magnitude, power factor
            distances = request.form.getlist("distance[]")
            I_mags    = request.form.getlist("I_mag[]")
            PFs       = request.form.getlist("PF[]")

            load_points = []
            for d_str, Im_str, pf_str in zip(distances, I_mags, PFs):
                if d_str and Im_str and pf_str:
                    d  = float(d_str)
                    Im = float(Im_str)
                    pf = float(pf_str)
                    # φ = arccos(pf), current lags → negative angle
                    phi = math.acos(pf)
                    I_complex = cmath.rect(Im, -phi)
                    load_points.append((d, I_complex))

            # 4. Calculate & format
            voltages = calculate_voltages(V_s, total_length, z_per_meter, load_points)
            result = []
            for dist, V in sorted(voltages.items()):
                result.append({
                    "distance": dist,
                    "magnitude": round(abs(V), 2),
                    "angle":     round(math.degrees(cmath.phase(V)), 2)
                })

            return render_template("index.html", result=result)

        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
