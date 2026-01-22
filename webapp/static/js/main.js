// initial state
let state = {
    x: -3.0,
    y: 0.5,
    v: 8.0,
    angle: 60.0,
    rim_width: 1.0, 
    rim_height: 2.0
};

let layout = {
    traj: {},
    polar: {},
    budget: {}
};

let isUpdating = false;
let updatePending = false;

// Elements
const trajDiv = document.getElementById('traj-plot');
const polarDiv = document.getElementById('polar-plot');
const budgetDiv = document.getElementById('budget-plot');

async function init() {
    const response = await fetch('/init_data');
    const data = await response.json();
    
    state.rim_width = data.rim_width;
    state.rim_height = data.rim_height;
    
    // Setup Trajectory Plot
    const heatmapTrace = {
        x: data.heatmap.x,
        y: data.heatmap.y,
        z: data.heatmap.z,
        type: 'heatmap',
        colorscale: 'Viridis',
        showscale: false,
        hoverinfo: 'none'
    };
    
    const trajTrace = {
        x: [],
        y: [],
        mode: 'lines',
        line: {color: 'rgb(0, 255, 0)', width: 3},
        name: 'Trajectory'
    };
    
    const shooterTrace = {
        x: [state.x],
        y: [state.y],
        mode: 'markers',
        marker: {color: 'black', size: 12, symbol: 'circle'},
        type: 'scatter',
        name: 'Shooter'
    };
    
    const rimShape = {
        type: 'rect',
        x0: -state.rim_width/2,
        y0: 0, 
        x1: state.rim_width/2,
        y1: data.rim_height,
        line: {color: 'gray', width: 2},
        fillcolor: 'rgba(0,0,0,0)'
    };
    
    // Position tolerance box (initially hidden or zero)
    const posBoxShape = {
        type: 'rect',
        x0: 0,
        y0: 0,
        x1: 0,
        y1: 0.1,
        line: {width: 0},
        fillcolor: 'rgba(255, 255, 0, 0.5)' // Yellow semi-transparent
    };

    const hubShape = {
        type: 'rect',
        x0: -1.02,
        y0: 0,
        x1: 1.02,
        y1: 0.57,
        line: {color: 'rgb(80, 80, 80)', width: 2},
        fillcolor: 'rgba(0,0,0,0)'
    };
    
    const floorShape = {
        type: 'rect',
        x0: -6,
        y0: -0.5,
        x1: 1,
        y1: 0,
        line: {color: 'rgba(0,0,0,0)'},
        fillcolor: 'gray'
    };

    layout.traj = {
        title: 'Trajectory View (Click to move shooter)',
        xaxis: {range: [-6.2, 1], title: 'x (m)', fixedrange: true}, // fixed range prevents zoom/pan
        yaxis: {range: [-0.1, 4], title: 'y (m)', scaleanchor: 'x', scalemaker: 1, fixedrange: true},
        shapes: [floorShape, posBoxShape, hubShape, rimShape],
        margin: {t: 30, b: 30, l: 30, r: 30},
        hovermode: false,
        dragmode: false // Handle drag manually
    };
    
    Plotly.newPlot(trajDiv, [heatmapTrace, trajTrace, shooterTrace], layout.traj, {displayModeBar: false});

    // Setup Polar Plot
    const zoneTrace = {
        r: [],
        theta: [],
        fill: 'toself',
        type: 'scatterpolar',
        fillcolor: 'rgba(0, 255, 0, 0.5)',
        line: {color: 'green'},
        mode: 'lines',
        hoverinfo: 'none'
    };
    
    const curStateTrace = {
        r: [state.v],
        theta: [state.angle],
        mode: 'markers',
        type: 'scatterpolar',
        marker: {color: 'red', size: 15, symbol: 'cross'},
        name: 'Current'
    };

    layout.polar = {
        // title: 'Angle-Speed Space (Click to adjust)', // for readability
        polar: {
            radialaxis: {range: [0, 15], visible: true},
            angularaxis: {
                direction: "counterclockwise",
                rotation: 0,
            }
        },
        margin: {t: 30, b: 30, l: 30, r: 30},
        dragmode: false,
        hovermode: 'closest',
        showlegend: false
    };
    
    Plotly.newPlot(polarDiv, [zoneTrace, curStateTrace], layout.polar, {displayModeBar: false});

    // Fix cursor disappearing
    setTimeout(() => {
        const cursorNone = polarDiv.querySelectorAll('.cursor-none');
        cursorNone.forEach(el => {
            el.classList.remove('cursor-none');
            el.style.cursor = 'crosshair';
        });
    }, 100);

    const observer = new MutationObserver(() => {
        const cursorNone = polarDiv.querySelectorAll('.cursor-none');
        cursorNone.forEach(el => {
            el.classList.remove('cursor-none');
            el.style.cursor = 'crosshair';
        });
    });
    observer.observe(polarDiv, { attributes: true, subtree: true, attributeFilter: ['class'] });

    // Setup Budget Plot
    const rangeTrace = {
        x: [0, 0], // min, max
        y: [0, 0], 
        mode: 'lines',
        line: {color: 'green', width: 50}, // thick line as bar
        name: 'Valid Range'
    };
    
    const currentVTrace = {
        x: [state.v],
        y: [0],
        mode: 'markers',
        marker: {color: 'red', size: 20},
        name: 'Current Speed'
    };
    
    layout.budget = {
        title: 'Velocity Budget',
        xaxis: {range: [0, 15], title: 'Speed (m/s)', fixedrange: true},
        yaxis: {showticklabels: false, range: [-1, 1], fixedrange: true},
        margin: {t: 30, b: 30, l: 30, r: 30},
        height: 150,
        dragmode: false,
        showlegend: false
    };
    
    Plotly.newPlot(budgetDiv, [rangeTrace, currentVTrace], layout.budget, {displayModeBar: false});

    // Add Interaction Listeners
    setupInteractions();
    
    // Initial fetch
    updateData();
}

function setupInteractions() {
    let isDraggingTraj = false;
    let isDraggingPolar = false;
    let isDraggingBudget = false;

    // Trajectory Interaction
    trajDiv.addEventListener('mousedown', (e) => {
        isDraggingTraj = true;
        handleTrajMove(e);
    });
    
    trajDiv.addEventListener('mousemove', (e) => {
        if(isDraggingTraj) handleTrajMove(e);
    });
    
    trajDiv.addEventListener('mouseup', () => isDraggingTraj = false);
    trajDiv.addEventListener('mouseleave', () => isDraggingTraj = false);
    
    // Polar Interaction
    polarDiv.addEventListener('mousedown', (e) => {
        isDraggingPolar = true;
        handlePolarMove(e);
    });
    
    polarDiv.addEventListener('mousemove', (e) => {
        if(isDraggingPolar) handlePolarMove(e);
    });
    
    polarDiv.addEventListener('mouseup', () => isDraggingPolar = false);
    polarDiv.addEventListener('mouseleave', () => isDraggingPolar = false);

    // Budget Interaction
    budgetDiv.addEventListener('mousedown', (e) => {
        isDraggingBudget = true;
        handleBudgetMove(e);
    });

    budgetDiv.addEventListener('mousemove', (e) => {
        if(isDraggingBudget) handleBudgetMove(e);
    });

    budgetDiv.addEventListener('mouseup', () => isDraggingBudget = false);
    budgetDiv.addEventListener('mouseleave', () => isDraggingBudget = false);
    
    // Touch support (basic)
    trajDiv.addEventListener('touchstart', (e) => {
        isDraggingTraj = true;
        handleTrajMove(e.touches[0]);
        e.preventDefault();
    });
    trajDiv.addEventListener('touchmove', (e) => {
        if(isDraggingTraj) handleTrajMove(e.touches[0]);
        e.preventDefault(); 
    });
    
    polarDiv.addEventListener('touchstart', (e) => {
        isDraggingPolar = true;
        handlePolarMove(e.touches[0]);
         e.preventDefault();
    });
    polarDiv.addEventListener('touchmove', (e) => {
        if(isDraggingPolar) handlePolarMove(e.touches[0]);
         e.preventDefault();
    });

    budgetDiv.addEventListener('touchstart', (e) => {
        isDraggingBudget = true;
        handleBudgetMove(e.touches[0]);
        e.preventDefault();
    });
    budgetDiv.addEventListener('touchmove', (e) => {
        if(isDraggingBudget) handleBudgetMove(e.touches[0]);
        e.preventDefault();
    });
}

function handleTrajMove(e) {    
    const rect = trajDiv.getBoundingClientRect();
    const plotArea = trajDiv._fullLayout; // access internal layout for converters
    const xaxis = plotArea.xaxis;
    const yaxis = plotArea.yaxis;
    
    const xPx = e.clientX - rect.left - plotArea.margin.l;
    const yPx = e.clientY - rect.top - plotArea.margin.t;
    
    const dataX = xaxis.p2c(xPx);
    const dataY = yaxis.p2c(yPx);
    
    // Clamp if needed
    state.x = Math.max(-6.2, Math.min(1, dataX));
    state.y = Math.max(0, Math.min(4, dataY));
    
    scheduleUpdate();
}

function handleBudgetMove(e) {
    const rect = budgetDiv.getBoundingClientRect();
    const plotArea = budgetDiv._fullLayout;
    
    // Check if plot is ready
    if (!plotArea || !plotArea.xaxis) return;
    
    const xaxis = plotArea.xaxis;
    const xPx = e.clientX - rect.left - plotArea.margin.l;
    const dataX = xaxis.p2c(xPx); // This gives speed
    
    const newV = Math.max(0, Math.min(15, dataX));
    
    state.v = newV;
    scheduleUpdate();
}

function handlePolarMove(e) {
    // Convert pixel to polar r, theta
    
    const layout = polarDiv._fullLayout;
    
    // Calculate center relative to the container based on margins and size
    const width = layout.width;
    const height = layout.height;
    const margin = layout.margin;
    
    // Center of the plotting area
    const cx = margin.l + (width - margin.l - margin.r) / 2;
    const cy = margin.t + (height - margin.t - margin.b) / 2;
    
    // Coordinates relative to plot div
    const rect = polarDiv.getBoundingClientRect();
    const x = e.clientX - rect.left - cx;
    const y = e.clientY - rect.top - cy;
    
    // Standard Cartesian to Polar
    // Note: y is positive down in DOM. In Plotly polar with standard orientation (0 at 3 o'clock, CCW):
    // atan2(-y, x) gives angle from x-axis (right), increasing CCW.
    // direction "counterclockwise", rotation 0.
    
    const r = Math.sqrt(x*x + y*y);

    // Calculate scaling factor
    const plotWidth = width - margin.l - margin.r;
    const plotHeight = height - margin.t - margin.b;
    const maxRadiusPx = Math.min(plotWidth, plotHeight) / 2;
    
    // Max data value from layout
    const maxR = layout.polar.radialaxis.range[1]; 
    
    const dataR = (r / maxRadiusPx) * maxR;
    
    let theta = Math.atan2(-y, x) * (180 / Math.PI); // -y to flip y axis (screen coords) to cartesian
    if (theta < 0) theta += 360;
    
    if (dataR < maxR * 1.1) { // allow small overflow
        state.v = Math.max(0, dataR); // Clamp non-negative
        state.angle = theta;
        scheduleUpdate();
    }
}

function scheduleUpdate() {
    if (!isUpdating) {
        isUpdating = true;
        updateData().then(() => {
            isUpdating = false;
            if(updatePending) {
                updatePending = false;
                scheduleUpdate();
            }
        });
    } else {
        updatePending = true;
    }
}

async function updateData() {
    // show the update 
    Plotly.restyle(trajDiv, {x: [[state.x]], y: [[state.y]]}, [2]); 
    Plotly.restyle(polarDiv, {r: [[state.v]], theta: [[state.angle]]}, [1]);
    Plotly.restyle(budgetDiv, {x: [[state.v]]}, [1]);

    // fetch server for updated data
    try {
        const response = await fetch('/update_shot', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(state)
        });
        
        const data = await response.json();
        
        // update with new data
        
        // Trajectory
        const trajColor = data.result == 'make' ? 'rgb(0, 255, 0)' : 'rgb(255, 0, 0)';
        Plotly.restyle(trajDiv, {
            x: [data.trajectory.x], 
            y: [data.trajectory.y],
            'line.color': trajColor
        }, [1]);

        // shape index 1 in shapes array: [floor, posBox, hub, rim]
        if (data.pos_budget) {
            const minX = data.pos_budget.min_x;
            const maxX = data.pos_budget.max_x;
            // Only show if valid range exists
            let opacity = 0;
            if (Math.abs(maxX - minX) > 0.01) {
                opacity = 0.5;
            }
            
            const updateSchema = {
                'shapes[1].x0': minX,
                'shapes[1].x1': maxX,
                'shapes[1].y0': 0,
                'shapes[1].y1': 3.0, 
                'shapes[1].fillcolor': `rgba(255, 255, 0, ${opacity})`
            };
            
            // Update title with stats
            const xErr = (data.pos_budget.plus + data.pos_budget.minus).toFixed(2);
            const titleStats = `Pos: ${state.x.toFixed(2)}m | Speed: ${state.v.toFixed(2)}m/s | Angle: ${state.angle.toFixed(1)}° | X-Error: ±${xErr}m`;
            updateSchema['title.text'] = titleStats;
            
            Plotly.relayout(trajDiv, updateSchema);
        }
        
        // Polar Zones
        // Check if data.polar_zone contains valid arrays
        if(data.polar_zone && data.polar_zone.angles) {
            // Construct polygon from lower and upper bounds
            // r = [lower..., upper_reversed...]
            // theta = [angles..., angles_reversed...]
            
            const angles = data.polar_zone.angles;
            const lowers = data.polar_zone.lower_speeds;
            const uppers = data.polar_zone.upper_speeds;
            
            const rPoly = [...lowers, ...uppers.reverse()];
            const tPoly = [...angles, ...[...angles].reverse()]; // reverse creates new array
            
            Plotly.restyle(polarDiv, {
                r: [rPoly],
                theta: [tPoly]
            }, [0]);
        }
        
        // Budget
        // Range line

        Plotly.restyle(budgetDiv, {
            x: [[data.budget.min, data.budget.max]]
        }, [0]);
        
        // Update budget lines if we could
        const budgetShapes = [
            {
                type: 'line',
                x0: data.budget.min, y0: -0.5,
                x1: data.budget.min, y1: 0.5,
                line: {color: 'orange', width: 2, dash: 'dash'}
            },
            {
                type: 'line',
                x0: data.budget.max, y0: -0.5,
                x1: data.budget.max, y1: 0.5,
                line: {color: 'blue', width: 2, dash: 'dash'}
            }
        ];
        
        const fbRange = (data.budget.max - data.budget.min).toFixed(2);
        
        Plotly.relayout(budgetDiv, {
            'shapes': budgetShapes,
            'title.text': `Velocity Error Budget: Total tolerance = ${fbRange} m/s`
        });
        
    } catch (e) {
        console.error(e);
    }
}

init();
