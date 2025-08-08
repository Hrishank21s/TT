from flask import Flask, request, jsonify
from datetime import datetime
import json
import os

app = Flask(__name__)

# File to store table data
DATA_FILE = 'table_data.json'

# Initialize tables data
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        return {f"table_{i}": {"status": "available", "start_time": None, "total_time": 0, "rate": 50} 
                for i in range(1, 21)}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

tables = load_data()

@app.route('/')
def index():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pool Table Timer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .table-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .table-card.running {
            background-color: #e8f5e8;
            border: 2px solid #4caf50;
        }
        .table-card.paused {
            background-color: #fff3cd;
            border: 2px solid #ffc107;
        }
        .timer {
            font-size: 24px;
            font-weight: bold;
            margin: 15px 0;
            color: #333;
        }
        .cost {
            font-size: 18px;
            color: #007bff;
            margin: 10px 0;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .start-btn { background-color: #4caf50; color: white; }
        .pause-btn { background-color: #ff9800; color: white; }
        .resume-btn { background-color: #2196f3; color: white; }
        .end-btn { background-color: #f44336; color: white; }
        button:disabled { 
            background-color: #ccc; 
            cursor: not-allowed; 
        }
        .status {
            font-weight: bold;
            margin: 10px 0;
        }
        .available { color: #4caf50; }
        .running { color: #ff5722; }
        .paused { color: #ff9800; }
    </style>
</head>
<body>
    <h1>Pool Table Timer System</h1>
    <div class="container">"""
    
    # Generate table cards
    for table_id, table_data in tables.items():
        table_name = table_id.replace('_', ' ').title()
        status = table_data['status'].title()
        
        html_content += f"""
        <div class="table-card" id="card-{table_id}">
            <h2>{table_name}</h2>
            <div class="status" id="status-{table_id}">{status}</div>
            <div class="timer" id="timer-{table_id}">00:00:00</div>
            <div class="cost" id="cost-{table_id}">Cost: $0.00</div>
            
            <div class="controls">
                <button class="start-btn" onclick="startTable('{table_id}')">Start</button>
                <button class="pause-btn" onclick="pauseTable('{table_id}')">Pause</button>
                <button class="resume-btn" onclick="resumeTable('{table_id}')">Resume</button>
                <button class="end-btn" onclick="endTable('{table_id}')">End & Bill</button>
            </div>
        </div>"""
    
    html_content += """
    </div>

    <script>
        // Global variables to track timers
        const timers = {};
        const RATE_PER_HOUR = 50;
        const tables = """ + json.dumps(tables) + """;
        
        // Initialize tables on page load
        window.addEventListener('load', function() {
            initializeTables();
        });
        
        function initializeTables() {
            Object.keys(tables).forEach(tableId => {
                const tableData = tables[tableId];
                updateTableDisplay(tableId, tableData);
                
                if (tableData.status === 'running' && tableData.start_time) {
                    startClientTimer(tableId, tableData.start_time, tableData.total_time || 0);
                }
            });
        }
        
        function updateTableDisplay(tableId, data) {
            const card = document.getElementById(`card-${tableId}`);
            const status = document.getElementById(`status-${tableId}`);
            const buttons = card.querySelectorAll('button');
            
            // Update status
            status.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            status.className = `status ${data.status}`;
            
            // Update card appearance
            card.className = `table-card ${data.status}`;
            
            // Update button states
            buttons.forEach(btn => btn.disabled = false);
            
            if (data.status === 'available') {
                buttons[1].disabled = true; // pause
                buttons[2].disabled = true; // resume
                buttons[3].disabled = true; // end
            } else if (data.status === 'running') {
                buttons[0].disabled = true; // start
                buttons[2].disabled = true; // resume
            } else if (data.status === 'paused') {
                buttons[0].disabled = true; // start
                buttons[1].disabled = true; // pause
            }
        }
        
        function startClientTimer(tableId, startTime, previousTime = 0) {
            if (timers[tableId]) {
                clearInterval(timers[tableId]);
            }
            
            const startDateTime = new Date(startTime);
            
            timers[tableId] = setInterval(() => {
                const now = new Date();
                const currentSessionTime = (now - startDateTime) / 1000; // seconds
                const totalTime = previousTime + currentSessionTime;
                
                updateTimerDisplay(tableId, totalTime);
            }, 1000);
        }
        
        function updateTimerDisplay(tableId, totalSeconds) {
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = Math.floor(totalSeconds % 60);
            
            const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            const cost = (totalSeconds / 3600) * RATE_PER_HOUR;
            
            document.getElementById(`timer-${tableId}`).textContent = timeString;
            document.getElementById(`cost-${tableId}`).textContent = `Cost: $${cost.toFixed(2)}`;
        }
        
        function stopClientTimer(tableId) {
            if (timers[tableId]) {
                clearInterval(timers[tableId]);
                delete timers[tableId];
            }
        }
        
        async function startTable(tableId) {
            try {
                const response = await fetch(`/start_table/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    updateTableDisplay(tableId, data);
                    startClientTimer(tableId, data.start_time);
                }
            } catch (error) {
                console.error('Error starting table:', error);
            }
        }
        
        async function pauseTable(tableId) {
            try {
                const response = await fetch(`/pause_table/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    stopClientTimer(tableId);
                    updateTableDisplay(tableId, data);
                    updateTimerDisplay(tableId, data.total_time);
                }
            } catch (error) {
                console.error('Error pausing table:', error);
            }
        }
        
        async function resumeTable(tableId) {
            try {
                const response = await fetch(`/resume_table/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    updateTableDisplay(tableId, data);
                    
                    // Get current total time from server
                    const statusResponse = await fetch(`/get_table_status/${tableId}`);
                    const statusData = await statusResponse.json();
                    
                    startClientTimer(tableId, data.start_time, statusData.total_time || 0);
                }
            } catch (error) {
                console.error('Error resuming table:', error);
            }
        }
        
        async function endTable(tableId) {
            try {
                const response = await fetch(`/end_table/${tableId}`);
                const data = await response.json();
                
                if (data.success) {
                    stopClientTimer(tableId);
                    
                    alert(`Table ended!\\nTotal Time: ${data.total_hours.toFixed(2)} hours\\nTotal Cost: $${data.total_cost}`);
                    
                    // Reset display
                    updateTableDisplay(tableId, { status: 'available' });
                    document.getElementById(`timer-${tableId}`).textContent = '00:00:00';
                    document.getElementById(`cost-${tableId}`).textContent = 'Cost: $0.00';
                }
            } catch (error) {
                console.error('Error ending table:', error);
            }
        }
    </script>
</body>
</html>"""
    
    return html_content

@app.route('/start_table/<table_id>')
def start_table(table_id):
    if table_id in tables and tables[table_id]['status'] == 'available':
        tables[table_id]['status'] = 'running'
        tables[table_id]['start_time'] = datetime.now().isoformat()
        save_data(tables)
        return jsonify({
            'success': True, 
            'start_time': tables[table_id]['start_time'],
            'status': 'running'
        })
    return jsonify({'success': False})

@app.route('/pause_table/<table_id>')
def pause_table(table_id):
    if table_id in tables and tables[table_id]['status'] == 'running':
        start_time = datetime.fromisoformat(tables[table_id]['start_time'])
        elapsed = (datetime.now() - start_time).total_seconds()
        tables[table_id]['total_time'] += elapsed
        tables[table_id]['status'] = 'paused'
        tables[table_id]['start_time'] = None
        save_data(tables)
        return jsonify({
            'success': True,
            'total_time': tables[table_id]['total_time'],
            'status': 'paused'
        })
    return jsonify({'success': False})

@app.route('/resume_table/<table_id>')
def resume_table(table_id):
    if table_id in tables and tables[table_id]['status'] == 'paused':
        tables[table_id]['status'] = 'running'
        tables[table_id]['start_time'] = datetime.now().isoformat()
        save_data(tables)
        return jsonify({
            'success': True,
            'start_time': tables[table_id]['start_time'],
            'status': 'running'
        })
    return jsonify({'success': False})

@app.route('/end_table/<table_id>')
def end_table(table_id):
    if table_id in tables:
        if tables[table_id]['status'] == 'running':
            start_time = datetime.fromisoformat(tables[table_id]['start_time'])
            elapsed = (datetime.now() - start_time).total_seconds()
            tables[table_id]['total_time'] += elapsed
        
        total_hours = tables[table_id]['total_time'] / 3600
        total_cost = total_hours * tables[table_id]['rate']
        
        # Reset table
        tables[table_id] = {
            "status": "available", 
            "start_time": None, 
            "total_time": 0, 
            "rate": 50
        }
        save_data(tables)
        
        return jsonify({
            'success': True,
            'total_cost': round(total_cost, 2),
            'total_hours': round(total_hours, 2)
        })
    return jsonify({'success': False})

@app.route('/get_table_status/<table_id>')
def get_table_status(table_id):
    if table_id in tables:
        return jsonify(tables[table_id])
    return jsonify({'error': 'Table not found'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
