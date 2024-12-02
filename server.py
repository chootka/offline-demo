from flask import Flask, jsonify, Response, render_template
import socket
import json
from datetime import datetime
from queue import Queue
import threading
import time

app = Flask(__name__)
message_queue = Queue()
latest_packets = []

def load_sample_data():
    try:
        with open('data/sample_packets.json', 'r') as f:
            data = json.load(f)
            print(f"Loaded {len(data['packets'])} sample packets")
            for packet in data['packets']:
                latest_packets.append(packet)
                message_queue.put(packet)
                time.sleep(0.5)
            print("Finished loading sample data")
    except Exception as e:
        print(f"Error loading sample data: {e}")

def listen_for_js8():
    try:
        print("Starting listener...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ('127.0.0.1', 2237)
        sock.connect(server_address)
        print("Connected to UDP server successfully")
        
        while True:
            try:
                print("Receiving data...")
                print(f"Socket: {sock}")
                data = sock.recv(1024)
                print(f"Received data: {data}")
                timestamp = datetime.now().timestamp()
                packet_data = {
                    'timestamp': timestamp,
                    'raw_data': [b for b in data],
                    'size': len(data)
                }
                print(f"Packet data: {packet_data}")
                latest_packets.append(packet_data)
                if len(latest_packets) > 100:
                    latest_packets.pop(0)
                message_queue.put(packet_data)
                print(f"Received UDP packet: size={len(data)} bytes")
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
    except Exception as e:
        print(f"Could not connect to UDP server: {e}")
        print("Falling back to sample data...")
        load_sample_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def generate():
        while True:
            print("Generating packet...")
            packet = message_queue.get()
            print(f"Packet: {packet}")
            print(f"Sending packet: size={packet['size']}")
            yield f"data: {json.dumps(packet)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    print("Starting server...")
    # listener_thread = threading.Thread(target=listen_for_js8)
    listener_thread = threading.Thread(target=load_sample_data)
    listener_thread.daemon = True
    listener_thread.start()
    app.run(debug=True)
