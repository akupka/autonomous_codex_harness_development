#!/usr/bin/env python3
"""
Dashboard Server for Autonomous Codex Harness
Provides web-based monitoring and metrics visualization
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for dashboard endpoints."""
    
    def _send_json(self, data: dict[str, Any], status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_html(self, content: str):
        """Send HTML response."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(content.encode())
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # API endpoints
        if path == "/api/metrics":
            self._handle_metrics()
        elif path == "/api/status":
            self._handle_status()
        elif path == "/api/git":
            self._handle_git()
        elif path == "/api/logs":
            self._handle_logs()
        elif path == "/api/control":
            self._handle_control_status()
        elif path == "/" or path == "/index.html":
            self._serve_dashboard()
        else:
            self.send_error(404, "Not found")
    
    def do_POST(self):
        """Handle POST requests for control actions."""
        parsed = urlparse(self.path)
        
        if parsed.path == "/api/control":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode())
            self._handle_control_action(data)
        else:
            self.send_error(404, "Not found")
    
    def _handle_metrics(self):
        """Return metrics summary."""
        metrics_file = Path("harness_metrics.jsonl")
        
        if not metrics_file.exists():
            self._send_json({
                "total_cycles": 0,
                "successful_cycles": 0,
                "recent_cycles": []
            })
            return
        
        lines = metrics_file.read_text().strip().split("\n")
        entries = [json.loads(line) for line in lines if line]
        
        if not entries:
            self._send_json({
                "total_cycles": 0,
                "successful_cycles": 0,
                "recent_cycles": []
            })
            return
        
        successful = sum(1 for e in entries if e.get("success", False))
        total_progress = sum(e.get("progress", 0) for e in entries)
        avg_duration = sum(e.get("duration_secs", 0) for e in entries) / len(entries) if entries else 0
        timeout_count = sum(1 for e in entries if e.get("timeout", False))
        error_rate = (len(entries) - successful) / len(entries) if len(entries) > 0 else 0
        
        # Get recent 20 cycles
        recent = entries[-20:] if len(entries) > 20 else entries
        
        self._send_json({
            "total_cycles": len(entries),
            "successful_cycles": successful,
            "failed_cycles": len(entries) - successful,
            "total_tests_fixed": total_progress,
            "avg_cycle_duration": round(avg_duration, 2),
            "error_rate": round(error_rate, 3),
            "timeout_count": timeout_count,
            "recent_cycles": recent,
            "last_update": datetime.now().isoformat()
        })
    
    def _handle_status(self):
        """Return current test status."""
        feature_file = Path("feature_list.json")
        
        if not feature_file.exists():
            self._send_json({"error": "feature_list.json not found"}, 404)
            return
        
        try:
            data = json.loads(feature_file.read_text())
            tests = data.get("tests") if isinstance(data, dict) else data
            
            total = len(tests)
            passing = sum(1 for t in tests if t.get("passes", False))
            failing = total - passing
            
            # Group by category
            categories = {}
            for test in tests:
                cat = test.get("category", "Unknown")
                if cat not in categories:
                    categories[cat] = {"total": 0, "passing": 0, "failing": 0}
                categories[cat]["total"] += 1
                if test.get("passes", False):
                    categories[cat]["passing"] += 1
                else:
                    categories[cat]["failing"] += 1
            
            # Get failing tests details
            failing_tests = [
                {
                    "category": t.get("category", "Unknown"),
                    "description": t.get("description", "")
                }
                for t in tests if not t.get("passes", False)
            ]
            
            self._send_json({
                "total_tests": total,
                "passing_tests": passing,
                "failing_tests": failing,
                "pass_rate": round(passing / total * 100, 1) if total > 0 else 0,
                "categories": categories,
                "failing_details": failing_tests[:10],  # First 10
                "last_update": datetime.now().isoformat()
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _handle_git(self):
        """Return git history and checkpoints."""
        try:
            # Recent commits
            result = subprocess.run(
                ["git", "log", "--oneline", "-20"],
                capture_output=True,
                text=True,
                check=True
            )
            commits = result.stdout.strip().split("\n")
            
            # Checkpoints
            result = subprocess.run(
                ["git", "tag", "-l", "checkpoint-*"],
                capture_output=True,
                text=True,
                check=True
            )
            checkpoints = result.stdout.strip().split("\n") if result.stdout.strip() else []
            
            # Current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            
            self._send_json({
                "branch": branch,
                "recent_commits": commits,
                "checkpoints": checkpoints[-10:],  # Last 10
                "last_update": datetime.now().isoformat()
            })
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _handle_logs(self):
        """Return recent log files."""
        log_dir = Path("logs")
        
        if not log_dir.exists():
            self._send_json({"logs": []})
            return
        
        try:
            # Match cycle_*.log pattern (new) and run_*.log (legacy)
            log_files = sorted(
                list(log_dir.glob("cycle_*.log")) + list(log_dir.glob("run_*.log")),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )[:10]  # Last 10
            
            logs = []
            for log_file in log_files:
                stat = log_file.stat()
                logs.append({
                    "filename": log_file.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "preview": self._read_log_preview(log_file)
                })
            
            self._send_json({"logs": logs})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
    
    def _read_log_preview(self, log_file: Path) -> str:
        """Read last 10 lines of log file."""
        try:
            result = subprocess.run(
                ["tail", "-10", str(log_file)],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except:
            return ""
    
    def _handle_control_status(self):
        """Check control file status."""
        pause_exists = Path(".harness_pause").exists()
        stop_exists = Path(".harness_stop").exists()
        
        # Check if harness is running
        try:
            result = subprocess.run(
                ["pgrep", "-f", "run_until_green.sh"],
                capture_output=True,
                check=False
            )
            running = result.returncode == 0
        except:
            running = False
        
        self._send_json({
            "running": running,
            "paused": pause_exists,
            "stop_requested": stop_exists
        })
    
    def _handle_control_action(self, data: dict):
        """Handle control actions (pause/resume/stop)."""
        action = data.get("action")
        
        try:
            if action == "pause":
                Path(".harness_pause").touch()
                self._send_json({"status": "ok", "message": "Pause requested"})
            elif action == "resume":
                if Path(".harness_pause").exists():
                    Path(".harness_pause").unlink()
                self._send_json({"status": "ok", "message": "Resume requested"})
            elif action == "stop":
                Path(".harness_stop").touch()
                self._send_json({"status": "ok", "message": "Stop requested"})
            else:
                self._send_json({"status": "error", "message": "Unknown action"}, 400)
        except Exception as e:
            self._send_json({"status": "error", "message": str(e)}, 500)
    
    def _serve_dashboard(self):
        """Serve the main dashboard HTML."""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Codex Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { margin-bottom: 30px; color: #58a6ff; }
        h2 { margin: 20px 0 10px; color: #8b949e; font-size: 18px; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 20px;
        }
        
        .stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #21262d;
        }
        .stat:last-child { border-bottom: none; }
        .stat-label { color: #8b949e; }
        .stat-value { font-size: 24px; font-weight: bold; color: #58a6ff; }
        
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #0d1117;
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #238636, #2ea043);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background: #2ea043; }
        .status-paused { background: #f0883e; }
        .status-stopped { background: #da3633; }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        button {
            padding: 8px 16px;
            border: 1px solid #30363d;
            border-radius: 6px;
            background: #21262d;
            color: #c9d1d9;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover { background: #30363d; }
        button:active { background: #161b22; }
        
        .btn-pause { border-color: #f0883e; color: #f0883e; }
        .btn-stop { border-color: #da3633; color: #da3633; }
        .btn-resume { border-color: #2ea043; color: #2ea043; }
        
        .log-entry {
            background: #0d1117;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
        }
        
        .cycle-list {
            max-height: 300px;
            overflow-y: auto;
        }
        
        .cycle-item {
            padding: 8px;
            margin: 4px 0;
            background: #0d1117;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .cycle-success { border-left: 3px solid #2ea043; }
        .cycle-failed { border-left: 3px solid #da3633; }
        
        .badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        }
        .badge-success { background: #2ea043; color: white; }
        .badge-error { background: #da3633; color: white; }
        .badge-timeout { background: #f0883e; color: white; }
        
        .checkpoint-list {
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .checkpoint-item {
            padding: 4px 8px;
            margin: 2px 0;
            background: #0d1117;
            border-radius: 3px;
        }
        
        .refresh-info {
            text-align: right;
            color: #6e7681;
            font-size: 12px;
            margin-top: 10px;
        }
        
        .error { color: #f85149; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Autonomous Codex Dashboard</h1>
        
        <div class="grid">
            <!-- Status Card -->
            <div class="card">
                <h2>Status</h2>
                <div id="status-info">Loading...</div>
                <div class="controls">
                    <button class="btn-pause" onclick="sendControl('pause')">⏸ Pause</button>
                    <button class="btn-resume" onclick="sendControl('resume')">▶ Resume</button>
                    <button class="btn-stop" onclick="sendControl('stop')">⏹ Stop</button>
                </div>
            </div>
            
            <!-- Test Progress Card -->
            <div class="card">
                <h2>Test Progress</h2>
                <div id="test-progress">Loading...</div>
            </div>
            
            <!-- Metrics Card -->
            <div class="card">
                <h2>Cycle Metrics</h2>
                <div id="metrics-info">Loading...</div>
            </div>
        </div>
        
        <!-- Recent Cycles -->
        <div class="card">
            <h2>Recent Cycles</h2>
            <div id="recent-cycles" class="cycle-list">Loading...</div>
        </div>
        
        <div class="grid">
            <!-- Git Info -->
            <div class="card">
                <h2>Git & Checkpoints</h2>
                <div id="git-info">Loading...</div>
            </div>
            
            <!-- Recent Logs -->
            <div class="card">
                <h2>Recent Logs</h2>
                <div id="logs-info">Loading...</div>
            </div>
        </div>
        
        <div class="refresh-info">Auto-refresh every 5 seconds</div>
    </div>
    
    <script>
        let refreshInterval;
        
        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                return await response.json();
            } catch (e) {
                console.error(`Error fetching ${endpoint}:`, e);
                return null;
            }
        }
        
        async function sendControl(action) {
            try {
                const response = await fetch('/api/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action })
                });
                const data = await response.json();
                alert(data.message || data.status);
                updateDashboard();
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function updateDashboard() {
            // Status
            const control = await fetchData('/api/control');
            if (control) {
                let statusHtml = '<div class="stat">';
                statusHtml += '<span class="stat-label">';
                if (control.running) {
                    statusHtml += '<span class="status-indicator status-running"></span>Running';
                } else {
                    statusHtml += '<span class="status-indicator status-stopped"></span>Stopped';
                }
                if (control.paused) {
                    statusHtml += ' <span class="badge badge-timeout">PAUSED</span>';
                }
                if (control.stop_requested) {
                    statusHtml += ' <span class="badge badge-error">STOP REQUESTED</span>';
                }
                statusHtml += '</span></div>';
                document.getElementById('status-info').innerHTML = statusHtml;
            }
            
            // Test Progress
            const status = await fetchData('/api/status');
            if (status && !status.error) {
                const passRate = status.pass_rate || 0;
                let html = `
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${passRate}%">
                            ${passRate.toFixed(1)}%
                        </div>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Passing</span>
                        <span class="stat-value" style="color: #2ea043">${status.passing_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Failing</span>
                        <span class="stat-value" style="color: #da3633">${status.failing_tests}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Total</span>
                        <span class="stat-value">${status.total_tests}</span>
                    </div>
                `;
                document.getElementById('test-progress').innerHTML = html;
            }
            
            // Metrics
            const metrics = await fetchData('/api/metrics');
            if (metrics) {
                const successRate = metrics.total_cycles > 0 
                    ? ((1 - metrics.error_rate) * 100).toFixed(1)
                    : '0.0';
                const avgDuration = metrics.avg_cycle_duration || 0;
                const testsFixed = metrics.total_tests_fixed || 0;
                
                let html = `
                    <div class="stat">
                        <span class="stat-label">Total Cycles</span>
                        <span class="stat-value">${metrics.total_cycles}</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Success Rate</span>
                        <span class="stat-value">${successRate}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Avg Duration</span>
                        <span class="stat-value">${Math.round(avgDuration)}s</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Tests Fixed</span>
                        <span class="stat-value" style="color: #2ea043">${testsFixed}</span>
                    </div>
                `;
                document.getElementById('metrics-info').innerHTML = html;
                
                // Recent cycles
                if (metrics.recent_cycles && metrics.recent_cycles.length > 0) {
                    let cyclesHtml = '';
                    for (const cycle of metrics.recent_cycles.reverse()) {
                        const cssClass = cycle.success ? 'cycle-success' : 'cycle-failed';
                        const badge = cycle.success 
                            ? '<span class="badge badge-success">✓</span>' 
                            : cycle.timeout 
                                ? '<span class="badge badge-timeout">TIMEOUT</span>'
                                : '<span class="badge badge-error">ERROR</span>';
                        const progress = cycle.progress || 0;
                        const failingAfter = cycle.failing_after || 0;
                        const duration = Math.round(cycle.duration_secs || 0);
                        
                        cyclesHtml += `
                            <div class="cycle-item ${cssClass}">
                                <div>
                                    ${badge}
                                    <strong>#${cycle.iteration}</strong>
                                    Progress: ${progress > 0 ? '+' + progress : progress}
                                    (${failingAfter} failing)
                                </div>
                                <div>${duration}s</div>
                            </div>
                        `;
                    }
                    document.getElementById('recent-cycles').innerHTML = cyclesHtml;
                } else {
                    document.getElementById('recent-cycles').innerHTML = 'No cycles yet';
                }
            }
            
            // Git info
            const git = await fetchData('/api/git');
            if (git && !git.error) {
                let html = `<div class="stat"><span class="stat-label">Branch</span><span>${git.branch}</span></div>`;
                html += '<h3 style="margin-top: 15px; color: #8b949e;">Recent Commits</h3>';
                html += '<div style="font-family: monospace; font-size: 12px;">';
                for (const commit of git.recent_commits.slice(0, 5)) {
                    html += `<div style="padding: 4px 0;">${commit}</div>`;
                }
                html += '</div>';
                
                if (git.checkpoints.length > 0) {
                    html += '<h3 style="margin-top: 15px; color: #8b949e;">Checkpoints</h3>';
                    html += '<div class="checkpoint-list">';
                    for (const checkpoint of git.checkpoints) {
                        html += `<div class="checkpoint-item">🏷 ${checkpoint}</div>`;
                    }
                    html += '</div>';
                }
                document.getElementById('git-info').innerHTML = html;
            }
            
            // Logs
            const logs = await fetchData('/api/logs');
            if (logs && logs.logs) {
                let html = '';
                for (const log of logs.logs.slice(0, 5)) {
                    html += `
                        <div style="margin: 10px 0;">
                            <strong>${log.filename}</strong>
                            <span style="color: #6e7681; font-size: 11px;">
                                (${(log.size / 1024).toFixed(1)} KB)
                            </span>
                        </div>
                    `;
                }
                document.getElementById('logs-info').innerHTML = html || 'No logs yet';
            }
        }
        
        // Initial load and auto-refresh
        updateDashboard();
        refreshInterval = setInterval(updateDashboard, 5000);
    </script>
</body>
</html>"""
        self._send_html(html)


def main():
    """Start the dashboard server."""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    
    # Change to project root
    os.chdir(Path(__file__).parent.parent)
    
    print(f"🚀 Starting Autonomous Codex Dashboard")
    print(f"📊 Dashboard URL: http://localhost:{port}")
    print(f"🔄 Auto-refresh: 5 seconds")
    print(f"⏹  Press Ctrl+C to stop")
    print()
    
    with socketserver.TCPServer(("", port), DashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")


if __name__ == "__main__":
    main()
