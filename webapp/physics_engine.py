import numpy as np
from functools import lru_cache
from numpy import arctan2, cos, degrees, pi, radians, sin, sqrt, tan
from scipy.integrate import quad
from scipy.optimize import fsolve

g = 9.81
rim_width = 1.04  # 41 inches
rim_height = 1.83  # 72 inches
cargo_radius = 0.15 / 2  # radius in meters

# Precomputed heatmap data
heatmap_data = None
HEATMAP_X_RANGE = np.arange(-6, -1, 0.1)
HEATMAP_Y_RANGE = np.arange(0.2, 1.25, 0.1)

def get_speed_func_squared(startpt, endpt):
    x0, y0 = startpt
    x1, y1 = endpt
    return lambda a: (0.5 * g / (y0 - y1 + (x1 - x0) * tan(a))) * ((x1 - x0) / cos(a)) ** 2

@lru_cache(maxsize=512)
def get_ang_speed_space(xpos, ypos):
    f_far_squared = get_speed_func_squared((xpos, ypos), (rim_width / 2, rim_height))
    f_near_squared = get_speed_func_squared((xpos, ypos), (-rim_width / 2, rim_height))
    
    f_squared_diff = lambda a: f_far_squared(a) - f_near_squared(a)
    
    try:
        rad85 = radians(85) # try 85 radians as initial guess
        intersection = fsolve(f_squared_diff, rad85)[0]
    except:
        intersection = rad85
        
    ang_lower_bound = max(intersection, radians(5))
    ang_upper_bound = radians(85)
    
    f_far = lambda a: np.sqrt(np.maximum(0, f_far_squared(a)))
    f_near = lambda a: np.sqrt(np.maximum(0, f_near_squared(a)))
    f_diff = lambda a: f_far(a) - f_near(a)
    
    # Calculate area
    try:
        area, _ = quad(f_diff, ang_lower_bound, ang_upper_bound)
    except:
        area = 0

    # Generate points for the "green shading" polygon
    angles_deg = np.linspace(degrees(ang_lower_bound), degrees(ang_upper_bound), num=50)
    angles_rad = np.radians(angles_deg)
    
    lower_speeds = np.vectorize(f_near)(angles_rad)
    upper_speeds = np.vectorize(f_far)(angles_rad)
    
    return {
        "area": area,
        "angles": angles_deg.tolist(),
        "lower_speeds": lower_speeds.tolist(),
        "upper_speeds": upper_speeds.tolist()
    }

def calculate_trajectory(x0, y0, v, angle_rad):
    vx = v * cos(angle_rad)
    vy = v * sin(angle_rad)
    
    if vx == 0:
        return [], []
        
    t_total = 2.0 # Simulate 2 seconds or until ground
    t_pts = np.linspace(0, t_total, 100)
    
    xs = x0 + vx * t_pts
    ys = y0 + vy * t_pts - 0.5 * g * t_pts**2
    
    # Filter ground hits for plotting
    valid_idx = ys >= 0
    xs = xs[valid_idx]
    ys = ys[valid_idx]
    
    return xs.tolist(), ys.tolist()

def check_shot(x0, y0, v, angle_rad):
    # Rim is at y = rim_height, x between -rim_width/2 and rim_width/2
    
    # Solve for t when y(t) = rim_height
    # rim_height = y0 + vy*t - 0.5*g*t^2
    # 0.5*g*t^2 - vy*t + (rim_height - y0) = 0
    
    vx = v * cos(angle_rad)
    vy = v * sin(angle_rad)
    
    delta_y = rim_height - y0
    
    # Quadratic eq: ax^2 + bx + c = 0
    a = 0.5 * g
    b = -vy
    c = delta_y
    
    disc = b**2 - 4*a*c
    
    result = "miss" # default
    
    if disc >= 0:
        t1 = (-b + sqrt(disc)) / (2*a)
        t2 = (-b - sqrt(disc)) / (2*a)
        
        ts = [t for t in [t1, t2] if t > 0]
        
        for t in ts:
            x_at_rim = x0 + vx * t
            vy_at_rim = vy - g * t
            
            # Check if within rim width
            # Original code: 
            # undershot if x < -rim_width/2
            # overshot if x > rim_width/2 - cargo_radius (Wait, asymmetric?)
            
            # "result = -1 (undershot) if solution.y[0][-1] < -rim_width/2"
            # "result = 1 (overshot) if solution.y[0][-1] > rim_width / 2 - cargo_radius"
            # And it stops when passed_rim or hit_rim.
            
            # If at y=rim_height it's within range, then its green.
            
            if vy_at_rim < 0:
                if x_at_rim >= -rim_width/2 and x_at_rim <= (rim_width/2 - cargo_radius):
                    result = "make"
                    break
                elif x_at_rim < -rim_width/2:
                    result = "short"
                else:
                    result = "long"
            
    return result

def get_velocity_budget(x0, y0, angle_rad):
    
    # valid range is [-rim_width/2, rim_width/2 - cargo_radius]
    
    v_min_sq_func = get_speed_func_squared((x0, y0), (-rim_width/2, rim_height))
    v_max_sq_func = get_speed_func_squared((x0, y0), (rim_width/2 - cargo_radius, rim_height))
    
    # speed squared at angle a
    try:
        v_min = sqrt(v_min_sq_func(angle_rad))
        v_max = sqrt(v_max_sq_func(angle_rad))
    except:
        v_min = 0
        v_max = 0
        
    return v_min, v_max

def get_position_budget(x0, y0, v, angle_rad):
    # x_at_rim = (x0 + dx) + vx * t
    # where t is time to reach y=rim_height.
    # Time t depends on y0 (fixed), vy (fixed).
    # t = (vy + sqrt(vy^2 - 2g(rim_height - y0))) / g  (falling solution)
    
    # x_at_rim = x0 + dx + vx * t
    # min_x - x0 - vx*t <= dx <= max_x - x0 - vx*t
    
    vx = v * cos(angle_rad)
    vy = v * sin(angle_rad)
    delta_y = rim_height - y0
    
    if vy**2 < 2*g*delta_y:
        return 0, 0, 0, 0 # Doesn't reach height
        
    t = (vy + sqrt(vy**2 - 2*g*delta_y)) / g
    
    # Target X interval
    x_target_min = -rim_width/2
    x_target_max = rim_width/2 - cargo_radius
    
    # x_arrival = x_start + vx * t
    # x_start = x_arrival - vx * t
    
    x_req_min = x_target_min - vx * t
    x_req_max = x_target_max - vx * t
    
    valid_min = x_req_min
    valid_max = x_req_max
    
    margin_left = max(0, x0 - valid_min)
    margin_right = max(0, valid_max - x0)
    
    # Check if x0 is actually valid first?
    if x0 < valid_min or x0 > valid_max:
         # "Ghost" budget - maybe negative? 
         # return 0,0 ensures we don't draw weird stuff if missed
         pass

    return margin_left, margin_right, valid_min, valid_max

def generate_heatmap():
    global heatmap_data
    if heatmap_data is not None:
        return heatmap_data

    # Grid calculation
    # xx, yy = np.meshgrid(HEATMAP_X_RANGE, HEATMAP_Y_RANGE)
    
    grid = []
    
    for _, x in enumerate(HEATMAP_X_RANGE):
        row = []
        for _, y in enumerate(HEATMAP_Y_RANGE):
            res = get_ang_speed_space(x, y)
            area = res['area']
            val = area * arctan2(rim_width, abs(x))
            row.append(val)
        grid.append(row)
        
    heatmap_data = {
        "x": HEATMAP_X_RANGE.tolist(),
        "y": HEATMAP_Y_RANGE.tolist(),
        "z": np.array(grid).T.tolist()
    }
    return heatmap_data

