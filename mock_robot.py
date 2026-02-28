#!/usr/bin/env python3
"""
Mock Robot Server — simulates robot_wifi.py without actual hardware.
Run:  python3 mock_robot.py
Then hit the 📡 button in the Sim (set robot URL to http://localhost:8080).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

HIP_MAP = {140:'forward_max', 115:'forward', 90:'neutral', 65:'backward', 40:'backward_max'}
KNEE_MAP = {150:'retracted_max', 120:'retracted', 90:'neutral', 60:'extended', 30:'extended_max'}
JOINT_NAMES = ['FR_Hip','FL_Hip','FL_Knee','FR_Knee','BR_Hip','BL_Hip','BR_Knee','BL_Knee']
MAPS = [HIP_MAP,HIP_MAP,KNEE_MAP,KNEE_MAP,HIP_MAP,HIP_MAP,KNEE_MAP,KNEE_MAP]

class RobotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(length))
        command = body.get('command')
        params  = body.get('params')

        print(f"\n{'='*50}")
        print(f"📨 Command: {command}")
        if params:
            for i, frame in enumerate(params):
                angles = frame.get('angles', [])
                dur    = frame.get('duration', '?')
                labels = [m.get(a, f'angle={a}') for m, a in zip(MAPS, angles)]
                pairs  = [f"{n}={l}" for n, l in zip(JOINT_NAMES, labels)]
                print(f"  Frame {i+1} ({dur}ms): {' | '.join(pairs)}")
        print(f"{'='*50}")

        resp = json.dumps({"status": "200", "msg": command}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(resp)

    def do_OPTIONS(self):      # CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, *_): pass   # 静默 access log

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), RobotHandler)
    print("🤖 Mock Robot Server running at http://localhost:8080")
    print("   → Set robot URL in Sim to: http://localhost:8080")
    server.serve_forever()
