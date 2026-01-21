# Trajectory Optimizer Scripts

## What These Do

Find the **best shooting position and speed** that gives you the most flywheel drop tolerance.

**Problem:** Your flywheel spins down when shooting multiple balls rapidly. Where should you position on the field to maximize how much your flywheel can drop before you start missing?

**Solution:** These scripts find the optimal distance, starting speed, and show you exactly how much your flywheel velocity can drop.

---

## Two Versions

- **`optimize_trajectory_drag.py`** - With air resistance (more realistic)
- **`optimize_trajectory_nodrag.py`** - Without air resistance (simpler physics)

**Recommendation:** Use the drag version for real robot planning.

---

## Basic Usage

### Quick Start:

```bash
python3 optimize_trajectory_drag.py --angle 55 --y_pos 0.5 --x_pos 3.0
```

**Required arguments:**

- `--angle` - Launch angle in degrees (e.g., 55)
- `--y_pos` - Shooter height in meters (e.g., 0.5)
- `--x_pos` - Approximate distance from goal (e.g., 3.0)

### What You Get:

```
OPTIMAL CONFIGURATION FOUND
================================================================================
Shooting Distance (x):  3.10 m
Launch Angle:           55.0°
================================================================================

SHOOTING STRATEGY:
  START at speed:       9.20 m/s   SET FLYWHEEL HERE
  Can drop to:          7.80 m/s
  FLYWHEEL DROP TOL:    1.40 m/s   THIS IS YOUR ANSWER
================================================================================

POSITION ERROR TOLERANCE:
  TOTAL X-TOLERANCE:    ±0.65 m
```

**Translation:**

- Position your robot 3.1m from the goal
- Set flywheel to 9.2 m/s
- You can shoot until flywheel drops to 7.8 m/s (1.4 m/s drop)
- You have ±0.65m positioning error forgiveness

Plus you get **2 plots** showing trajectory and flywheel tolerance visually.

---

## Global Search (Find Best Position Anywhere)

Don't know where to shoot from? Search the entire field:

```bash
python3 optimize_trajectory_drag.py --angle 55 --y_pos 0.5 --global_search
```

This searches **1.5m to 8m** and finds the absolute best position for that angle.

Takes ~10-20 seconds but shows progress updates.

---

## Common Examples

### Example 1: Test a specific position

```bash
python3 optimize_trajectory_drag.py --angle 60 --y_pos 0.6 --x_pos 2.5
```

### Example 2: Find best position globally

```bash
python3 optimize_trajectory_drag.py --angle 60 --y_pos 0.6 --global_search
```

### Example 3: Compare different angles

```bash
python3 optimize_trajectory_drag.py --angle 45 --y_pos 0.5 --global_search
python3 optimize_trajectory_drag.py --angle 55 --y_pos 0.5 --global_search
python3 optimize_trajectory_drag.py --angle 65 --y_pos 0.5 --global_search
```

Compare the flywheel drop tolerances to pick the best angle!

---

## Understanding the Output

### Key Numbers:

**START at speed: 9.20 m/s**
→ Set your flywheel to this speed

**FLYWHEEL DROP TOL: 1.40 m/s**
→ Your flywheel can drop 1.4 m/s before you miss
→ Bigger number = more shots before needing recovery

**TOTAL X-TOLERANCE: ±0.65 m**
→ You can be off by 65cm in positioning and still make shots

### The Plots:

**Top Plot:** Shows your trajectory and yellow zone where you can position

**Bottom Plot:** Shows flywheel drop range visually with arrow

---

## Real-World Application

**Scenario:** Shooting 3 balls rapidly

1. Run optimizer:

```bash
python3 optimize_trajectory_drag.py --angle 55 --y_pos 0.5 --x_pos 3.0
```

2. Result says: `FLYWHEEL DROP TOL: 1.40 m/s`, `START at: 9.2 m/s`

3. Interpretation:

   - Start at 9.2 m/s
   - Each shot, flywheel drops ~0.3 m/s
   - Ball 1: 9.2 m/s ✓
   - Ball 2: 8.9 m/s ✓
   - Ball 3: 8.6 m/s ✓
   - Ball 4: 8.3 m/s ✓
   - Ball 5: 8.0 m/s ✓
   - Still have 0.2 m/s margin before missing!

4. Decision: Can shoot 4-5 balls before needing flywheel recovery

---

## Tips

✓ **Always use drag version** for real planning
✓ **Start with global search** to find optimal position
✓ **Test multiple angles** to find best overall strategy
✓ **Higher angles** often give more flywheel tolerance but need higher speeds
✓ **Check position tolerance** - make sure you can actually position that accurately

---

## Parameters (Competition 2022)

Already configured in scripts:

- Goal height: 1.83m (72 inches)
- Goal width: 1.04m (42 inches)
- Ball radius: 0.075m
- Ball mass: 0.21kg
- Drag coefficient: 0.47

---

## Need More Details?

See **GLOBAL_SEARCH_GUIDE.md** for detailed global search usage
See **OPTIMIZER_USAGE.md** for comprehensive documentation

---

## Quick Troubleshooting

**"ERROR: No valid shooting configuration found!"**
→ Angle/position combination impossible - try different angle or closer/farther position

**Script runs but shows small flywheel tolerance (<0.5 m/s)**
→ Try different angle or use `--global_search` to find better position

**Takes too long**
→ Use local search (without `--global_search`) for faster results
