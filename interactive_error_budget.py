import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from numpy import arctan2, cos, degrees, pi, radians, sin, sqrt, tan
from scipy.integrate import quad, solve_ivp
from scipy.optimize import fsolve, minimize_scalar

# Updated parameters
g = 9.81
rim_width = 1.04  # 42 inches
rim_height = 1.83  # 72 inches
cargo_radius = 0.15 / 2  # radius of ball in meters


def flight_model(t, s):
    x, vx, y, vy = s
    dx = vx
    dvx = 0
    dy = vy
    dvy = -9.8
    return [dx, dvx, dy, dvy]


def hit_ground(t, s):
    x, vx, y, vy = s
    return y


hit_ground.terminal = True


def hit_rim(t, s):
    x, vx, y, vy = s
    dist_to_rim = min(x - -rim_width / 2, -(y - rim_height))
    return dist_to_rim + cargo_radius


hit_rim.terminal = True


def passed_rim(t, s):
    x, vx, y, vy = s
    return x - rim_width / 2


passed_rim.terminal = True


def try_shot(s0):
    t_span = (0, 5.0)
    solution = solve_ivp(
        flight_model, t_span, s0, events=[hit_ground, hit_rim, passed_rim], max_step=0.2
    )

    result = 0
    if solution.y[0][-1] < -rim_width / 2:
        result = -1
    elif solution.y[0][-1] > rim_width / 2 - cargo_radius:
        result = 1

    return result, solution.y[0, :], solution.y[2, :]


def get_speed_func_squared(startpt, endpt):
    x0, y0 = startpt
    x1, y1 = endpt
    return (
        lambda a: (0.5 * g / (y0 - y1 + (x1 - x0) * tan(a))) * ((x1 - x0) / cos(a)) ** 2
    )


def get_ang_speed_space(xpos, ypos):
    f_far_squared = get_speed_func_squared((xpos, ypos), (rim_width / 2, rim_height))
    f_near_squared = get_speed_func_squared((xpos, ypos), (-rim_width / 2, rim_height))
    f_squared_diff = lambda a: f_far_squared(a) - f_near_squared(a)
    intersection = fsolve(f_squared_diff, radians(85))[0]

    ang_lower_bound = max(intersection, radians(5))
    ang_upper_bound = radians(85)

    f_far = lambda a: sqrt(f_far_squared(a))
    f_near = lambda a: sqrt(f_near_squared(a))
    f_diff = lambda a: f_far(a) - f_near(a)
    area, error = quad(f_diff, ang_lower_bound, ang_upper_bound)

    angles = np.linspace(degrees(ang_lower_bound), degrees(ang_upper_bound), num=30)
    lower_bound_pts = np.vectorize(f_near)(radians(angles))
    upper_bound_pts = np.vectorize(f_far)(radians(angles))

    return area, angles, lower_bound_pts, upper_bound_pts


def calculate_velocity_tolerance(x_pos, y_pos, angle, nominal_speed):
    """
    For a given position and angle, calculate how much velocity can drop.
    Returns: (speed_minus, speed_plus) - how much slower/faster you can shoot
    """
    vx_nom = nominal_speed * cos(angle)
    vy_nom = nominal_speed * sin(angle)

    # Test slower speeds
    speed_minus = 0
    for dv in np.arange(0, 5, 0.1):
        test_speed = nominal_speed - dv
        if test_speed <= 0:
            break
        vx = test_speed * cos(angle)
        vy = test_speed * sin(angle)
        shoot_state = [x_pos, vx, y_pos, vy]
        result, _, _ = try_shot(shoot_state)
        if result == 0:
            speed_minus = dv
        else:
            break

    # Test faster speeds
    speed_plus = 0
    for dv in np.arange(0, 5, 0.1):
        test_speed = nominal_speed + dv
        vx = test_speed * cos(angle)
        vy = test_speed * sin(angle)
        shoot_state = [x_pos, vx, y_pos, vy]
        result, _, _ = try_shot(shoot_state)
        if result == 0:
            speed_plus = dv
        else:
            break

    return speed_minus, speed_plus


# Initial state
shoot_state = [-3.0, 8.0 * cos(radians(55)), 0.5, 8.0 * sin(radians(55))]
traj = [[], []]

# Create figure with 3 subplots
fig = plt.figure(figsize=(10, 12))
ax1 = plt.subplot(3, 1, 1)
ax2 = plt.subplot(3, 1, 2, projection="polar")
ax3 = plt.subplot(3, 1, 3)
fig.suptitle(
    "Position & Velocity Error Budget Analysis (NO DRAG)\nClick to explore error tolerances",
    fontsize=14,
    fontweight="bold",
)


def repaint_ax1():
    """Trajectory view with position error bounds."""
    ax1.clear()

    ax1.set_xlim([-6.2, 1])
    ax1.set_ylim([-0.1, 3])
    ax1.set_xlabel("x position (meters)", fontsize=10)
    ax1.set_ylabel("y position (meters)", fontsize=10)

    left, bottom, width, height = (-rim_width / 2, 0, rim_width, rim_height)
    ax1.add_patch(
        mpatches.Rectangle(
            (left, bottom), width, height, fill=False, color="gray", linewidth=2
        )
    )
    ax1.add_patch(
        mpatches.Rectangle((-6, -0.5), 7, 0.5, fill=True, color="gray", linewidth=2)
    )
    ax1.set_aspect("equal", adjustable="box")

    x_pos = shoot_state[0]
    y_pos = shoot_state[2]
    vx = shoot_state[1]
    vy = shoot_state[3]
    speed = sqrt(vx**2 + vy**2)
    angle = arctan2(vy, vx)

    # Plot nominal trajectory
    result, traj[0], traj[1] = try_shot(shoot_state)
    color_str = "green" if result == 0 else "red"
    ax1.plot(traj[0], traj[1], color_str, linewidth=2.5, alpha=0.8)

    # Calculate position tolerance (using fixed angle)
    error_minus = 0
    for dx in np.arange(0, 2, 0.05):
        test_x = x_pos + dx
        test_state = [test_x, vx, y_pos, vy]
        result, _, _ = try_shot(test_state)
        if result == 0:
            error_minus = dx
        else:
            break

    error_plus = 0
    for dx in np.arange(0, 2, 0.05):
        test_x = x_pos - dx
        test_state = [test_x, vx, y_pos, vy]
        result, _, _ = try_shot(test_state)
        if result == 0:
            error_plus = dx
        else:
            break

    # Show position error bounds
    if error_minus > 0 or error_plus > 0:
        ax1.axvline(x_pos - error_plus, color="orange", linestyle="--", alpha=0.7)
        ax1.axvline(x_pos + error_minus, color="orange", linestyle="--", alpha=0.7)
        ax1.fill_betweenx(
            [0, 3], x_pos - error_plus, x_pos + error_minus, alpha=0.2, color="yellow"
        )

    # Mark shooter position
    ax1.scatter(
        x_pos,
        y_pos,
        c="black",
        s=120,
        marker="o",
        zorder=5,
        edgecolors="white",
        linewidths=1.5,
    )

    ax1.set_title(
        f"Pos: {-x_pos:.2f}m | Speed: {speed:.1f}m/s | Angle: {degrees(angle):.1f}° | X-Error: ±{error_minus+error_plus:.2f}m",
        fontsize=11,
    )
    ax1.grid(True, alpha=0.2)


def repaint_ax2():
    """Polar plot for angle-speed space."""
    ax2.clear()

    x_pos = shoot_state[0]
    y_pos = shoot_state[2]
    vx = shoot_state[1]
    vy = shoot_state[3]

    area, angles, lower_bound_pts, upper_bound_pts = get_ang_speed_space(x_pos, y_pos)
    angles_rad = np.radians(angles)

    ax2.fill_between(
        angles_rad,
        lower_bound_pts,
        upper_bound_pts,
        color="lightgreen",
        alpha=0.5,
        label="Valid shot zone",
    )

    ax2.set_ylim([0, 15])
    ax2.set_theta_zero_location("E")
    ax2.set_theta_direction(1)
    ax2.set_thetamin(5)
    ax2.set_thetamax(85)
    ax2.set_title("Angle-Speed Space (Click to adjust)", fontsize=11, pad=20)
    ax2.grid(True, alpha=0.3)

    # Plot current shot
    angle_rad = arctan2(vy, vx)
    speed = sqrt(vx**2 + vy**2)
    ax2.scatter(
        angle_rad,
        speed,
        c="red",
        s=100,
        marker="X",
        zorder=5,
        edgecolors="darkred",
        linewidth=2,
    )
    ax2.legend(fontsize=9, loc="upper right")


def repaint_ax3():
    """Velocity tolerance plot with error bars."""
    ax3.clear()

    x_pos = shoot_state[0]
    y_pos = shoot_state[2]
    vx = shoot_state[1]
    vy = shoot_state[3]
    speed = sqrt(vx**2 + vy**2)
    angle = arctan2(vy, vx)

    # Calculate velocity tolerance
    speed_minus, speed_plus = calculate_velocity_tolerance(x_pos, y_pos, angle, speed)

    # Create error bar plot
    # Plot the acceptable speed range as a shaded region
    min_speed = speed - speed_minus
    max_speed = speed + speed_plus

    ax3.axvspan(
        min_speed, max_speed, alpha=0.2, color="green", label="Acceptable speed range"
    )

    # Plot error bars
    ax3.errorbar(
        speed,
        0.5,
        xerr=[[speed_minus], [speed_plus]],
        fmt="o",
        markersize=10,
        color="red",
        ecolor="black",
        elinewidth=3,
        capsize=10,
        capthick=3,
        label="Nominal speed",
        zorder=5,
    )

    # Mark the bounds
    ax3.axvline(
        min_speed,
        color="orange",
        linewidth=2,
        linestyle="--",
        label=f"Min: {min_speed:.2f} m/s (flywheel drop limit)",
        alpha=0.7,
    )
    ax3.axvline(
        max_speed,
        color="blue",
        linewidth=2,
        linestyle="--",
        label=f"Max: {max_speed:.2f} m/s",
        alpha=0.7,
    )

    # Annotations
    ax3.text(
        min_speed,
        0.8,
        f"-{speed_minus:.2f} m/s\n(Flywheel drop)",
        ha="center",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="orange", alpha=0.5),
    )
    ax3.text(
        max_speed,
        0.8,
        f"+{speed_plus:.2f} m/s",
        ha="center",
        fontsize=9,
        bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.5),
    )
    ax3.text(
        speed,
        0.2,
        f"{speed:.2f} m/s\nNominal",
        ha="center",
        fontsize=9,
        fontweight="bold",
    )

    ax3.set_xlabel("Launch Speed (m/s)", fontsize=11, fontweight="bold")
    ax3.set_ylabel("")
    ax3.set_yticks([])
    ax3.set_ylim([0, 1])
    ax3.set_xlim([max(0, min_speed - 0.5), max_speed + 0.5])
    ax3.set_title(
        f"Velocity Error Budget: Total tolerance = {speed_minus+speed_plus:.2f} m/s",
        fontsize=11,
        fontweight="bold",
    )
    ax3.grid(True, alpha=0.3, axis="x")
    ax3.legend(fontsize=8, loc="upper right")


def onHover(event):
    if event.button == 1:
        ix, iy = event.xdata, event.ydata

        if event.inaxes is ax1 and ix is not None and iy is not None:
            # Dragging in trajectory plot changes position
            if -6 < ix < -0.5 and 0.2 < iy < 1.5:
                shoot_state[0] = ix
                shoot_state[2] = iy

                repaint_ax1()
                repaint_ax2()
                repaint_ax3()
                plt.draw()

        if event.inaxes is ax2 and ix is not None and iy is not None:
            # Dragging in polar plot changes angle/speed
            angle = ix  # Already in radians
            speed = iy

            if speed > 0:
                shoot_state[1] = speed * cos(angle)
                shoot_state[3] = speed * sin(angle)

                repaint_ax1()
                repaint_ax2()
                repaint_ax3()
                plt.draw()


repaint_ax1()
repaint_ax2()
repaint_ax3()

fig.canvas.mpl_connect("motion_notify_event", onHover)
plt.tight_layout()
plt.show()
