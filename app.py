from flask import Flask, render_template, request, jsonify
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
    return render_template('index.html', tables=tables)

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

