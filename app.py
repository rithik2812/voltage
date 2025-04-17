from flask import Flask, render_template, request
import cmath, math

app = Flask(__name__)

def calculate_voltages(V_s, total_length, z_per_meter, load_points):
    loads = sorted(load_points, key=lambda x: x[0])
    distances = [d for d, _ in loads]
    currents = [I for _, I in loads]
    cum_currents = [sum(currents[i:], complex(0)) for i in range(len(currents))]

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
            # Source voltage
            V_mag = float(request.form["V_mag"])
            V_angle = float(request.form["V_angle"])
            V_s = cmath.rect(V_mag, math.radians(V_angle))

            # Feeder
            total_length = float(request.form["total_length"])
            R = float(request.form["R"])
            X = float(request.form["X"])
            z_per_meter = complex(R, X)

            # Loads: distance, current magnitude, PF, PF type
            ds = request.form.getlist("distance[]")
            Ims = request.form.getlist("I_mag[]")
            PFs = request.form.getlist("PF[]")
            types = request.form.getlist("PF_type[]")

            load_points = []
            for d_str, Im_str, pf_str, t in zip(ds, Ims, PFs, types):
                if d_str and Im_str and pf_str and t:
                    d = float(d_str)
                    Im = float(Im_str)
                    pf = float(pf_str)
                    if pf < 0 or pf > 1:
                        raise ValueError(f"Power Factor must be between 0 and 1, got {pf}")
                    phi = math.acos(pf)
                    angle = -phi if t == 'lagging' else phi
                    I_complex = cmath.rect(Im, angle)
                    load_points.append((d, I_complex))
            
            if not load_points:
                raise ValueError("No valid load points provided.")

            volts = calculate_voltages(V_s, total_length, z_per_meter, load_points)
            result = []
            for dist, V in volts.items():
                result.append({
                    'distance': dist,
                    'magnitude': round(abs(V), 2),
                    'angle': round(math.degrees(cmath.phase(V)), 2)
                })
            return render_template('index.html', result=result)
        except Exception as e:
            return render_template('index.html', error=str(e))
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
