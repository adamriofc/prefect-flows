"""
Remote Trigger Server - Trigger flows via HTTP API
Location: D:\Projects\PrefectFlows\remote_trigger_server.py
WSL Path: /mnt/d/Projects/PrefectFlows/remote_trigger_server.py

This creates a simple HTTP server that can trigger Prefect flows.
Combine with Ngrok or Cloudflare Tunnel for remote access.

Usage:
1. Run: python3 remote_trigger_server.py
2. Server starts on http://localhost:8080
3. Trigger flow: curl http://localhost:8080/trigger/hello?name=YourName

For remote access (optional):
- Install ngrok: https://ngrok.com
- Run: ngrok http 8080
- Use the ngrok URL to trigger remotely
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import subprocess
import threading
import os

# Configuration
HOST = "0.0.0.0"
PORT = 8080
FLOWS_DIR = "/mnt/d/Projects/PrefectFlows"


class TriggerHandler(BaseHTTPRequestHandler):
    """HTTP handler for flow triggers."""
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {
                "status": "ok",
                "message": "Prefect Remote Trigger Server",
                "endpoints": {
                    "/trigger/hello": "Trigger Hello World Flow",
                    "/trigger/custom?flow=<filename>": "Trigger custom flow",
                    "/health": "Health check",
                    "/flows": "List available flows",
                }
            }
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "healthy"}
            self.wfile.write(json.dumps(response).encode())
            
        elif path == "/flows":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            try:
                flows = [f for f in os.listdir(FLOWS_DIR) if f.endswith(".py")]
                response = {"flows": flows}
            except Exception as e:
                response = {"error": str(e)}
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        elif path == "/trigger/hello":
            name = params.get("name", ["OpenCode User"])[0]
            self.trigger_flow("hello_flow.py", {"name": name})
            
        elif path.startswith("/trigger/custom"):
            flow_file = params.get("flow", [None])[0]
            if flow_file:
                self.trigger_flow(flow_file, params)
            else:
                self.send_error(400, "Missing 'flow' parameter")
                
        else:
            self.send_error(404, "Not Found")
    
    def trigger_flow(self, flow_file: str, params: dict):
        """Trigger a flow file asynchronously."""
        def run_flow():
            try:
                flow_path = f"{FLOWS_DIR}/{flow_file}"
                result = subprocess.run(
                    ["python3", flow_path],
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=FLOWS_DIR
                )
                print(f"Flow {flow_file} completed with exit code {result.returncode}")
                if result.stdout:
                    print(f"Output: {result.stdout[-500:]}")  # Last 500 chars
                if result.stderr:
                    print(f"Errors: {result.stderr[-500:]}")
            except Exception as e:
                print(f"Error running flow: {e}")
        
        # Run flow in background thread
        thread = threading.Thread(target=run_flow)
        thread.start()
        
        self.send_response(202)  # Accepted
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "status": "accepted",
            "message": f"Flow {flow_file} triggered",
            "params": {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        }
        self.wfile.write(json.dumps(response, indent=2).encode())
    
    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{self.log_date_time_string()}] {args[0]}")


def main():
    """Start the trigger server."""
    print("=" * 60)
    print("Prefect Remote Trigger Server")
    print("=" * 60)
    print("")
    print(f"Server: http://localhost:{PORT}")
    print("")
    print("Endpoints:")
    print(f"  GET /                    - Server info")
    print(f"  GET /health              - Health check")
    print(f"  GET /flows               - List available flows")
    print(f"  GET /trigger/hello       - Trigger Hello World Flow")
    print(f"  GET /trigger/hello?name= - Trigger with custom name")
    print("")
    print("Example:")
    print(f"  curl http://localhost:{PORT}/trigger/hello?name=Adam")
    print("")
    print("For remote access, use ngrok:")
    print(f"  ngrok http {PORT}")
    print("")
    print("Press Ctrl+C to stop.")
    print("=" * 60)
    
    server = HTTPServer((HOST, PORT), TriggerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
