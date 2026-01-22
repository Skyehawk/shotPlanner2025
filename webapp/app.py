import numpy as np
import physics_engine as physics
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

physics.generate_heatmap()  # pre-generate heatmap


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/init_data", methods=["GET"])
def init_data():
    heatmap = physics.generate_heatmap()
    return jsonify(
        {
            "heatmap": heatmap,
            "rim_width": physics.rim_width,
            "rim_height": physics.rim_height,
            "cargo_radius": physics.cargo_radius,
        }
    )


@app.route("/update_shot", methods=["POST"])
def update_shot():
    # inital values
    data = request.json
    x = float(data.get("x", -3.0))
    y = float(data.get("y", 0.5))
    v = float(data.get("v", 8.0))
    angle_deg = float(data.get("angle", 60.0))
    angle_rad = np.radians(angle_deg)

    # 1. Trajectory
    traj_x, traj_y = physics.calculate_trajectory(x, y, v, angle_rad)

    # 2. Polar Plot Data (Green zone for THIS position)
    polar_data = physics.get_ang_speed_space(x, y)

    # 3. Budget for THIS angle
    v_min, v_max = physics.get_velocity_budget(x, y, angle_rad)

    # 4. Result
    result = physics.check_shot(x, y, v, angle_rad)

    # 5. Position Budget
    pos_minus, pos_plus, valid_x_min, valid_x_max = physics.get_position_budget(
        x, y, v, angle_rad
    )

    return jsonify(
        {
            "trajectory": {"x": traj_x, "y": traj_y},
            "polar_zone": polar_data,
            "budget": {"min": v_min, "max": v_max, "current": v},
            "pos_budget": {
                "minus": pos_minus,
                "plus": pos_plus,
                "min_x": valid_x_min,
                "max_x": valid_x_max,
            },
            "result": result,
        }
    )


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
