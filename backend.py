from flask import Flask, request, jsonify, send_file
import os
import logging
from scapy.all import *
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from main_script import (
    read_pcap, extract_packet_data, analyze_packet_data,
    extract_packet_data_security, detect_port_scanning
)

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logging.basicConfig(level=logging.INFO)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    port_scan_threshold = int(request.form.get('port_scan_threshold', 100))
    
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        packets = read_pcap(file_path)
        df = extract_packet_data(packets)
        total_bandwidth, protocol_counts, ip_communication_table, protocol_frequency, ip_communication_protocols = analyze_packet_data(df)
        detect_port_scanning(extract_packet_data_security(packets), port_scan_threshold)

        # Generate a protocol distribution plot
        plt.figure(figsize=(8, 5))
        protocol_counts.set_index('Protocol')['Count'].plot(kind='bar', color='skyblue', rot=45)
        plt.title('Protocol Distribution')
        plt.tight_layout()
        plot_file = BytesIO()
        plt.savefig(plot_file, format='png')
        plot_file.seek(0)

        return jsonify({
            "total_bandwidth": total_bandwidth,
            "protocol_counts": protocol_counts.to_dict(orient='records'),
            "ip_communication_table": ip_communication_table.to_dict(orient='records'),
            "warnings": f"Check for port scanning activity if present."
        }), 200
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
