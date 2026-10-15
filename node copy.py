import socket
import json
import os

# Render dynamically tells your app what port to use. We default to 8000 locally.
PORT = int(os.environ.get("PORT", 8000))
DATA_FILE = "internet_data.json"

# Initialize local database file if empty
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

# Start the raw master network server bound to '0.0.0.0' for public access
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', PORT))
server.listen()

print(f"🗄️ Master Internet Server Online on port {PORT}")

while True:
    client_socket, _ = server.accept()
    
    # Read the incoming transmission
    raw_request = client_socket.recv(4096).decode('utf-8')
    
    # Parse out the underlying packet (ignoring standard HTTP wrapper headers if present)
    lines = raw_request.split("\r\n")
    body = lines[-1].strip() if lines else ""
    request = body if ("|" in body) else raw_request.strip()
    
    network_db = load_network_data()
    response_payload = ""

    if request.startswith("VISIT|"):
        _, domain = request.split("|", 1)
        if domain in network_db:
            response_payload = f"FOUND|{network_db[domain]}"
        else:
            response_payload = f"NOT_FOUND|Error 404: Web address does not exist."
            
    elif request.startswith("CREATE|"):
        try:
            _, domain, content = request.split("|", 2)
            network_db[domain] = content
            save_network_data(network_db)
            response_payload = f"SUCCESS|Created/Updated address '{domain}'."
        except ValueError:
            response_payload = "ERROR|Invalid creation format."
    else:
        response_payload = "ERROR|Unknown network protocol instruction."
        
    # Send a compliant cloud response back to Render's router
    http_response = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/plain\r\n"
        f"Content-Length: {len(response_payload)}\r\n"
        "Connection: close\r\n\r\n"
        f"{response_payload}"
    )
    
    client_socket.send(http_response.encode('utf-8'))
    client_socket.close()
