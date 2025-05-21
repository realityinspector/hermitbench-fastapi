# Building a Flask Frontend for HermitBench API

This document provides step-by-step instructions for building a complete Flask web application that consumes the HermitBench API. The frontend will provide a user-friendly interface for running LLM autonomy benchmarks, viewing results, and generating reports.

## Overview

You'll be creating a Flask application that:
1. Connects to the HermitBench FastAPI backend
2. Provides intuitive forms for configuring and running benchmarks
3. Displays real-time results and progress
4. Visualizes model comparisons and summaries
5. Allows downloading of reports in various formats

## Prerequisites

- Python 3.11+
- Understanding of Flask web framework
- Knowledge of HTML, CSS, and JavaScript
- HermitBench API backend running (locally or remotely)

## Project Structure

```
flask-hermitbench/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── api_client.py
│   ├── forms.py
│   └── utils.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── run.html
│   ├── batch.html
│   ├── results.html
│   ├── compare.html
│   └── reports.html
├── config.py
└── run.py
```

## Step 1: Project Setup

1. Create the project directory structure
2. Install dependencies:
   ```bash
   pip install flask flask-wtf requests python-dotenv
   ```
3. Create the Flask application factory in `app/__init__.py`:
   ```python
   from flask import Flask
   from config import Config

   def create_app(config_class=Config):
       app = Flask(__name__)
       app.config.from_object(config_class)
       
       from app.routes import main
       app.register_blueprint(main)
       
       return app
   ```

## Step 2: API Client

Create an API client to interact with the HermitBench API in `app/api_client.py`:

```python
import requests
import json
from typing import Dict, List, Any, Optional

class HermitBenchClient:
    """Client for interacting with the HermitBench API."""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        
    def get_models(self) -> List[Dict[str, Any]]:
        """Get available LLM models."""
        response = requests.get(f"{self.base_url}/api/models")
        response.raise_for_status()
        return response.json()["models"]
    
    def run_interaction(self, model_name, temperature=0.7, top_p=1.0, max_turns=10):
        """Run a single autonomous interaction."""
        payload = {
            "model_name": model_name,
            "temperature": temperature,
            "top_p": top_p,
            "max_turns": max_turns
        }
        response = requests.post(f"{self.base_url}/api/run", json=payload)
        response.raise_for_status()
        return response.json()
    
    def run_batch(self, models, num_runs_per_model=1, temperature=0.7, top_p=1.0, max_turns=10, task_delay_ms=3000):
        """Start a batch of autonomous interactions."""
        payload = {
            "models": models,
            "num_runs_per_model": num_runs_per_model,
            "temperature": temperature,
            "top_p": top_p,
            "max_turns": max_turns,
            "task_delay_ms": task_delay_ms
        }
        response = requests.post(f"{self.base_url}/api/run-batch", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_batch_status(self, batch_id):
        """Get status of a batch run."""
        response = requests.get(f"{self.base_url}/api/batch/{batch_id}")
        response.raise_for_status()
        return response.json()
    
    def get_batch_results(self, batch_id):
        """Get results from a completed batch."""
        response = requests.get(f"{self.base_url}/api/batch/{batch_id}/results")
        response.raise_for_status()
        return response.json()
    
    def get_batch_summaries(self, batch_id):
        """Get model summaries from a completed batch."""
        response = requests.get(f"{self.base_url}/api/batch/{batch_id}/summaries")
        response.raise_for_status()
        return response.json()
    
    def generate_persona_cards(self, batch_id):
        """Generate model persona cards."""
        response = requests.post(f"{self.base_url}/api/batch/{batch_id}/personas")
        response.raise_for_status()
        return response.json()
    
    def generate_report(self, batch_id, report_type):
        """Generate a report for a batch."""
        payload = {"report_type": report_type}
        response = requests.post(f"{self.base_url}/api/batch/{batch_id}/report", json=payload)
        response.raise_for_status()
        return response.json()
    
    def run_test(self):
        """Run a standard test."""
        response = requests.post(f"{self.base_url}/api/test-run")
        response.raise_for_status()
        return response.json()
```

## Step 3: Forms

Create forms for user input in `app/forms.py`:

```python
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ApiConfigForm(FlaskForm):
    """Form for configuring the API connection."""
    api_url = StringField('API URL', validators=[DataRequired()], 
                         default='http://localhost:5000')
    submit = SubmitField('Save')

class SingleRunForm(FlaskForm):
    """Form for a single model run."""
    model_name = SelectMultipleField('Model', validators=[DataRequired()])
    temperature = FloatField('Temperature', validators=[NumberRange(min=0, max=2)], 
                            default=0.7)
    top_p = FloatField('Top P', validators=[NumberRange(min=0, max=1)], 
                      default=1.0)
    max_turns = IntegerField('Max Turns', validators=[NumberRange(min=1, max=50)], 
                           default=10)
    submit = SubmitField('Run Interaction')

class BatchRunForm(FlaskForm):
    """Form for a batch run with multiple models."""
    models = SelectMultipleField('Models', validators=[DataRequired()])
    num_runs_per_model = IntegerField('Runs Per Model', validators=[NumberRange(min=1, max=10)], 
                                    default=1)
    temperature = FloatField('Temperature', validators=[NumberRange(min=0, max=2)], 
                           default=0.7)
    top_p = FloatField('Top P', validators=[NumberRange(min=0, max=1)], 
                     default=1.0)
    max_turns = IntegerField('Max Turns', validators=[NumberRange(min=1, max=50)], 
                          default=10)
    task_delay_ms = IntegerField('Delay Between Tasks (ms)', validators=[NumberRange(min=0)], 
                               default=3000)
    submit = SubmitField('Start Batch Run')

class ReportForm(FlaskForm):
    """Form for generating reports."""
    report_type = SelectMultipleField('Report Type', 
                                    choices=[
                                        ('csv_results', 'All Results (CSV)'),
                                        ('csv_summary', 'Summary Table (CSV)'),
                                        ('detailed_scorecard', 'Detailed Scorecard (JSON)')
                                    ],
                                    validators=[DataRequired()])
    submit = SubmitField('Generate Report')
```

## Step 4: Routes

Create the routes to handle user requests in `app/routes.py`:

```python
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.forms import ApiConfigForm, SingleRunForm, BatchRunForm, ReportForm
from app.api_client import HermitBenchClient
import json
import os

main = Blueprint('main', __name__)

def get_api_client():
    """Get API client with current base URL."""
    base_url = session.get('api_url', 'http://localhost:5000')
    return HermitBenchClient(base_url)

@main.route('/', methods=['GET', 'POST'])
def index():
    """Home page with API configuration."""
    form = ApiConfigForm()
    if form.validate_on_submit():
        session['api_url'] = form.api_url.data
        flash('API URL saved', 'success')
        return redirect(url_for('main.index'))
    
    # Load current value from session
    if 'api_url' in session:
        form.api_url.data = session['api_url']
    
    return render_template('index.html', title='HermitBench UI', form=form)

@main.route('/models')
def models():
    """Page showing available models."""
    try:
        api_client = get_api_client()
        models = api_client.get_models()
        return render_template('models.html', title='Available Models', models=models)
    except Exception as e:
        flash(f"Error fetching models: {str(e)}", 'danger')
        return redirect(url_for('main.index'))

@main.route('/run', methods=['GET', 'POST'])
def run():
    """Page for running a single interaction."""
    form = SingleRunForm()
    
    # Populate model choices
    try:
        api_client = get_api_client()
        models = api_client.get_models()
        form.model_name.choices = [(m['id'], f"{m.get('name', m['id'])}") for m in models]
    except Exception as e:
        flash(f"Error fetching models: {str(e)}", 'danger')
        return redirect(url_for('main.index'))
    
    if form.validate_on_submit():
        try:
            result = api_client.run_interaction(
                model_name=form.model_name.data[0],  # First selected model
                temperature=form.temperature.data,
                top_p=form.top_p.data,
                max_turns=form.max_turns.data
            )
            return render_template('result.html', title='Run Result', result=result)
        except Exception as e:
            flash(f"Error running interaction: {str(e)}", 'danger')
    
    return render_template('run.html', title='Run Interaction', form=form)

@main.route('/batch', methods=['GET', 'POST'])
def batch():
    """Page for starting a batch run."""
    form = BatchRunForm()
    
    # Populate model choices
    try:
        api_client = get_api_client()
        models = api_client.get_models()
        form.models.choices = [(m['id'], f"{m.get('name', m['id'])}") for m in models]
    except Exception as e:
        flash(f"Error fetching models: {str(e)}", 'danger')
        return redirect(url_for('main.index'))
    
    if form.validate_on_submit():
        try:
            batch_result = api_client.run_batch(
                models=form.models.data,
                num_runs_per_model=form.num_runs_per_model.data,
                temperature=form.temperature.data,
                top_p=form.top_p.data,
                max_turns=form.max_turns.data,
                task_delay_ms=form.task_delay_ms.data
            )
            # Store batch ID in session
            session['current_batch_id'] = batch_result['batch_id']
            return redirect(url_for('main.batch_status', batch_id=batch_result['batch_id']))
        except Exception as e:
            flash(f"Error starting batch: {str(e)}", 'danger')
    
    return render_template('batch.html', title='Batch Run', form=form)

@main.route('/batch/<batch_id>/status')
def batch_status(batch_id):
    """Page showing batch run status."""
    try:
        api_client = get_api_client()
        status = api_client.get_batch_status(batch_id)
        
        # If completed, redirect to results
        if status['status'] == 'completed':
            return redirect(url_for('main.batch_results', batch_id=batch_id))
        
        return render_template('status.html', title='Batch Status', 
                             batch_id=batch_id, status=status)
    except Exception as e:
        flash(f"Error checking batch status: {str(e)}", 'danger')
        return redirect(url_for('main.index'))

@main.route('/batch/<batch_id>/results')
def batch_results(batch_id):
    """Page showing batch results."""
    try:
        api_client = get_api_client()
        results = api_client.get_batch_results(batch_id)
        summaries = api_client.get_batch_summaries(batch_id)
        
        return render_template('results.html', title='Batch Results', 
                             batch_id=batch_id, results=results, summaries=summaries)
    except Exception as e:
        flash(f"Error fetching batch results: {str(e)}", 'danger')
        return redirect(url_for('main.index'))

@main.route('/batch/<batch_id>/personas')
def generate_personas(batch_id):
    """Generate and show model personas."""
    try:
        api_client = get_api_client()
        personas = api_client.generate_persona_cards(batch_id)
        
        return render_template('personas.html', title='Model Personas', 
                             batch_id=batch_id, personas=personas)
    except Exception as e:
        flash(f"Error generating personas: {str(e)}", 'danger')
        return redirect(url_for('main.batch_results', batch_id=batch_id))

@main.route('/batch/<batch_id>/report', methods=['GET', 'POST'])
def generate_report(batch_id):
    """Page for generating reports."""
    form = ReportForm()
    
    if form.validate_on_submit():
        try:
            api_client = get_api_client()
            report = api_client.generate_report(batch_id, form.report_type.data[0])  # First selected type
            
            # Handle report download logic
            return render_template('report_download.html', title='Download Report', 
                                 batch_id=batch_id, report=report)
        except Exception as e:
            flash(f"Error generating report: {str(e)}", 'danger')
    
    return render_template('report.html', title='Generate Report', 
                         batch_id=batch_id, form=form)

@main.route('/test')
def run_test():
    """Run a standard test."""
    try:
        api_client = get_api_client()
        result = api_client.run_test()
        flash('Test run completed successfully', 'success')
        return redirect(url_for('main.batch_results', batch_id=result.get('batch_id')))
    except Exception as e:
        flash(f"Error running test: {str(e)}", 'danger')
        return redirect(url_for('main.index'))

# API status check endpoint
@main.route('/api-status')
def api_status():
    """Check if the API is reachable."""
    try:
        api_client = get_api_client()
        # Try to get models as a simple health check
        api_client.get_models()
        return jsonify({'status': 'connected'})
    except Exception:
        return jsonify({'status': 'disconnected'})
```

## Step 5: Templates

Create a base template with common elements in `templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}HermitBench UI{% endblock %}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.index') }}">HermitBench UI</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.index') }}">Home</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.models') }}">Models</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.run') }}">Single Run</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.batch') }}">Batch Run</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('main.run_test') }}">Run Test</a>
                    </li>
                </ul>
                <div class="ms-auto" id="api-status-indicator">
                    <span class="badge bg-secondary">API Status: Checking...</span>
                </div>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>

    <footer class="mt-5 py-3 bg-light">
        <div class="container text-center">
            <p class="text-muted">HermitBench UI - A Frontend for HermitBench API</p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
    <script>
        // Check API status every 10 seconds
        function checkApiStatus() {
            fetch('/api-status')
                .then(response => response.json())
                .then(data => {
                    const statusIndicator = document.getElementById('api-status-indicator');
                    if (data.status === 'connected') {
                        statusIndicator.innerHTML = '<span class="badge bg-success">API Status: Connected</span>';
                    } else {
                        statusIndicator.innerHTML = '<span class="badge bg-danger">API Status: Disconnected</span>';
                    }
                })
                .catch(() => {
                    document.getElementById('api-status-indicator').innerHTML = 
                        '<span class="badge bg-danger">API Status: Error</span>';
                });
        }
        
        // Initial check and set interval
        checkApiStatus();
        setInterval(checkApiStatus, 10000);
    </script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

Then create specific templates for each page. Here's an example for the homepage (`templates/index.html`):

```html
{% extends 'base.html' %}

{% block title %}HermitBench UI - Home{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h2>Welcome to HermitBench UI</h2>
            </div>
            <div class="card-body">
                <p class="lead">
                    This is a web interface for the HermitBench API, which allows you to run and evaluate
                    autonomous LLM interactions.
                </p>
                <p>
                    Configure the API connection below, then use the navigation menu to access different features.
                </p>
                
                <form method="POST" action="{{ url_for('main.index') }}">
                    {{ form.hidden_tag() }}
                    <div class="mb-3">
                        {{ form.api_url.label(class="form-label") }}
                        {{ form.api_url(class="form-control") }}
                        {% if form.api_url.errors %}
                            <div class="text-danger">
                                {% for error in form.api_url.errors %}
                                    <span>{{ error }}</span>
                                {% endfor %}
                            </div>
                        {% endif %}
                        <div class="form-text">Enter the base URL of the HermitBench API</div>
                    </div>
                    {{ form.submit(class="btn btn-primary") }}
                </form>
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h3>Quick Actions</h3>
            </div>
            <div class="card-body">
                <div class="d-grid gap-3">
                    <a href="{{ url_for('main.models') }}" class="btn btn-outline-primary">
                        Browse Available Models
                    </a>
                    <a href="{{ url_for('main.run') }}" class="btn btn-outline-primary">
                        Run Single Interaction
                    </a>
                    <a href="{{ url_for('main.batch') }}" class="btn btn-outline-primary">
                        Start Batch Run
                    </a>
                    <a href="{{ url_for('main.run_test') }}" class="btn btn-outline-secondary">
                        Run Standard Test
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

Develop similar templates for other pages: models.html, run.html, batch.html, status.html, results.html, personas.html, report.html, etc.

## Step 6: Configuration

Create the configuration file `config.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Flask application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-flask-hermitbench'
    
    # Default API URL
    DEFAULT_API_URL = os.environ.get('HERMITBENCH_API_URL') or 'http://localhost:5000'
```

## Step 7: Main Application Entry Point

Create the entry point in `run.py`:

```python
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

## Step 8: Static Files

Create key CSS and JavaScript files to enhance the UI:

### CSS (`static/css/style.css`):

```css
/* Custom styles for HermitBench UI */

/* Dashboard cards */
.dashboard-card {
    height: 100%;
    transition: transform 0.3s ease;
}

.dashboard-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

/* Results table */
.results-table {
    width: 100%;
    overflow-x: auto;
}

.model-card {
    border-left: 4px solid #007bff;
    margin-bottom: 20px;
}

/* Conversation transcript */
.conversation-transcript {
    max-height: 500px;
    overflow-y: auto;
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 5px;
}

.msg-system {
    color: #6c757d;
    font-style: italic;
}

.msg-user {
    color: #007bff;
    font-weight: bold;
}

.msg-assistant {
    color: #28a745;
}

.msg-system-note {
    color: #dc3545;
    font-size: 0.9em;
}

/* Progress bars */
.progress {
    height: 25px;
}

/* Charts */
.chart-container {
    position: relative;
    height: 300px;
    margin-bottom: 30px;
}

/* Model comparison table */
.comparison-table th {
    position: sticky;
    top: 0;
    background-color: #f8f9fa;
}

/* Metrics highlights */
.metric-card {
    text-align: center;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    background-color: #f8f9fa;
}

.metric-value {
    font-size: 2.5rem;
    font-weight: bold;
}

/* Form styling */
.form-container {
    max-width: 800px;
    margin: 0 auto;
}

/* Report download button */
.download-btn {
    display: inline-block;
    margin: 10px 0;
}
```

### JavaScript for Batch Status Updates (`static/js/batch-status.js`):

```javascript
// JavaScript for batch status page
document.addEventListener('DOMContentLoaded', function() {
    const batchId = document.getElementById('batch-id').value;
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    
    function updateStatus() {
        fetch(`/batch/${batchId}/status`)
            .then(response => response.json())
            .then(data => {
                // Update progress bar
                const progress = Math.round((data.completed_tasks / data.total_tasks) * 100);
                progressBar.style.width = `${progress}%`;
                progressBar.setAttribute('aria-valuenow', progress);
                progressBar.textContent = `${progress}%`;
                
                // Update status text
                statusText.textContent = `Status: ${data.status} (${data.completed_tasks}/${data.total_tasks} tasks completed)`;
                
                // If completed, redirect to results page
                if (data.status === 'completed') {
                    window.location.href = `/batch/${batchId}/results`;
                } else if (data.status === 'error') {
                    statusText.textContent = `Error: ${data.error}`;
                    statusText.classList.add('text-danger');
                } else {
                    // Check again in 2 seconds
                    setTimeout(updateStatus, 2000);
                }
            })
            .catch(error => {
                console.error('Error fetching batch status:', error);
                statusText.textContent = 'Error: Could not fetch batch status';
                statusText.classList.add('text-danger');
            });
    }
    
    // Start checking status
    updateStatus();
});
```

### JavaScript for Results Visualization (`static/js/results-charts.js`):

```javascript
// JavaScript for results visualization
document.addEventListener('DOMContentLoaded', function() {
    // Parse summary data from page
    const summariesData = JSON.parse(document.getElementById('summaries-data').textContent);
    
    // Prepare data for charts
    const modelNames = Object.keys(summariesData);
    const complianceRates = modelNames.map(model => summariesData[model].avg_compliance_rate * 100);
    const autonomyScores = modelNames.map(model => summariesData[model].avg_autonomy_score);
    const mirrorPassRates = modelNames.map(model => summariesData[model].mirror_test_pass_rate);
    
    // Set up colors
    const backgroundColors = [
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 99, 132, 0.5)',
        'rgba(75, 192, 192, 0.5)',
        'rgba(255, 159, 64, 0.5)',
        'rgba(153, 102, 255, 0.5)'
    ];
    
    // Compliance rate chart
    new Chart(
        document.getElementById('compliance-chart').getContext('2d'),
        {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [{
                    label: 'Compliance Rate (%)',
                    data: complianceRates,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(c => c.replace('0.5', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        }
    );
    
    // Autonomy score chart
    new Chart(
        document.getElementById('autonomy-chart').getContext('2d'),
        {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [{
                    label: 'Autonomy Score (0-10)',
                    data: autonomyScores,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(c => c.replace('0.5', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10
                    }
                }
            }
        }
    );
    
    // Mirror test pass rate chart
    new Chart(
        document.getElementById('mirror-test-chart').getContext('2d'),
        {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [{
                    label: 'Mirror Test Pass Rate (%)',
                    data: mirrorPassRates,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors.map(c => c.replace('0.5', '1')),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        }
    );
    
    // Create radar chart for model comparison
    const radarData = {
        labels: ['Compliance Rate', 'Autonomy Score', 'Mirror Test Pass Rate', 'Low Failures', 'Low Malformed Braces'],
        datasets: modelNames.map((model, index) => ({
            label: model,
            data: [
                summariesData[model].avg_compliance_rate * 10, // Scale to 0-10
                summariesData[model].avg_autonomy_score,
                summariesData[model].mirror_test_pass_rate / 10, // Scale to 0-10
                10 - Math.min(summariesData[model].avg_failures * 2, 10), // Invert and scale
                10 - Math.min(summariesData[model].avg_malformed_braces * 2, 10) // Invert and scale
            ],
            backgroundColor: backgroundColors[index % backgroundColors.length].replace('0.5', '0.2'),
            borderColor: backgroundColors[index % backgroundColors.length].replace('0.5', '1'),
            borderWidth: 2,
            pointBackgroundColor: backgroundColors[index % backgroundColors.length].replace('0.5', '1')
        }))
    };
    
    new Chart(
        document.getElementById('radar-chart').getContext('2d'),
        {
            type: 'radar',
            data: radarData,
            options: {
                responsive: true,
                scales: {
                    r: {
                        min: 0,
                        max: 10,
                        ticks: {
                            stepSize: 2
                        }
                    }
                }
            }
        }
    );
});
```

## Step 9: Running the Application

1. Create a requirements.txt file:
```
flask==2.2.3
flask-wtf==1.1.1
requests==2.28.2
python-dotenv==1.0.0
```

2. Final project structure should look like this:
```
flask-hermitbench/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   ├── api_client.py
│   ├── forms.py
│   └── utils.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── batch-status.js
│       └── results-charts.js
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── models.html
│   ├── run.html
│   ├── batch.html
│   ├── status.html
│   ├── results.html
│   ├── personas.html
│   └── report.html
├── config.py
├── run.py
└── requirements.txt
```

3. Run the application:
```bash
python run.py
```

4. Access the UI at http://localhost:5001

## Advanced Features to Implement

After completing the basic UI, consider enhancing the application with:

1. **Advanced Visualizations**: Add more complex visualizations using libraries like D3.js for deeper insights into model performance.

2. **Export Options**: Allow exporting visualizations as images or PDFs.

3. **User Accounts**: Implement basic user authentication to save preferences and previous runs.

4. **Custom Prompts**: Allow users to customize the system prompt for autonomy testing.

5. **Conversation Browser**: Create a dedicated interface for browsing through conversation transcripts with syntax highlighting for braced content.

6. **Custom CSS Themes**: Add light/dark mode toggle and other theme options.

7. **Mobile Optimization**: Ensure the UI works well on mobile devices.

8. **Websocket Support**: Implement real-time updates for batch status using websockets instead of polling.

This Flask frontend provides a complete user interface for working with the HermitBench API, making it accessible for users without requiring direct API interaction.