import socket
import json
import os

PORT = int(os.environ.get("PORT", 8000))
DATA_FILE = "internet_data.json"

if not os.path.exists(DATA_FILE):
    default_data = {
        "google.node": "Welcome to Google. Search for anything!",
        "wiki.node": "The free encyclopedia that anyone can edit.",
        "mytext.node": "This is my public text storage site."
    }
    with open(DATA_FILE, "w") as f:
        json.dump(default_data, f, indent=4)

def load_network_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_network_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', PORT))
server.listen()

print(f"🗄️ Cloud Server Parsing Engine Online on port {PORT}")

while True:
    client_socket, _ = server.accept()
    raw_request = client_socket.recv(4096).decode('utf-8')
    
    # --- PROXY EXTRACTION BUG FIX ---
    # Extract the true incoming payload body from the cloud delivery packet
    if "\r\n\r\n" in raw_request:
        request = raw_request.split("\r\n\r\n", 1)[1].strip()
    else:
        request = raw_request.strip()
        
    network_db = load_network_data()
    response_payload = ""

    if request.startswith("VISIT|"):
        _, domain = request.split("|", 1)
        if domain in network_db:
            response_payload = f"FOUND|{network_db[domain]}"
        else:
            response_payload = f"NOT_FOUND|Error 404: Web address '{domain}' does not exist."
            
    elif request.startswith("CREATE|"):
        try:
            _, domain, content = request.split("|", 2)
            network_db[domain] = content
            save_network_data(network_db)
            response_payload = f"SUCCESS|Created/Updated address '{domain}'."
        except ValueError:
            response_payload = "ERROR|Invalid creation format."
    else:
        # Fallback if standard web traffic hits the endpoint URL directly
        response_payload = "ERROR|Unknown network protocol instruction."
        
    # Send a compliant cloud response back to Render's edge proxies
    http_response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(response_payload)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Connection: close\r\n\r\n"
        f"{response_payload}"
    )
    
    client_socket.send(http_response.encode('utf-8'))
    client_socket.close()
