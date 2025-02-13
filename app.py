from flask import Flask, render_template, request, jsonify, Response
import requests

app = Flask(__name__)

# OctoPrint API Config
OCTOPRINT_URL = "http://192.168.1.233"  # URL von OctoPrint
API_KEY = "XXXX"  # Dein API-Key (Censored)

@app.route("/webcam")
def webcam_proxy():
    url = "http://192.168.1.233/webcam/?action=stream"
    response = requests.get(url, stream=True)
    return Response(response.iter_content(chunk_size=1024), content_type=response.headers['Content-Type'])


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"status": "error", "message": "Keine Datei hochgeladen"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Keine Datei ausgewählt"})

    try:
        url = f"{OCTOPRINT_URL}/api/files/local"
        headers = {"X-Api-Key": API_KEY}
        files = {"file": (file.filename, file.stream, file.mimetype)}
        response = requests.post(url, headers=headers, files=files)

        if response.status_code == 201:
            return jsonify({"status": "success", "message": "Datei erfolgreich hochgeladen"})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/files", methods=["GET"])
def get_files():
    try:
        url = f"{OCTOPRINT_URL}/api/files/local"
        headers = {"X-Api-Key": API_KEY}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            files = [
                f["name"] for f in response.json().get("files", []) if f["type"] == "machinecode"
            ]
            return jsonify({"status": "success", "files": files})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/select", methods=["POST"])
def select_file():
    try:
        filename = request.json.get("filename")
        if not filename:
            return jsonify({"status": "error", "message": "Keine Datei angegeben"})

        url = f"{OCTOPRINT_URL}/api/files/local/{filename}"
        headers = {"X-Api-Key": API_KEY}
        data = {"command": "select"}

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 204:
            return jsonify({"status": "success", "message": "Datei ausgewählt"})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/start", methods=["POST"])
def start_print():
    try:
        url = f"{OCTOPRINT_URL}/api/job"  # OctoPrint-Job-API
        headers = {"X-Api-Key": API_KEY}
        data = {"command": "start"}  # Der Befehl zum Starten eines Drucks
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 204:  # HTTP 204 No Content bedeutet Erfolg
            return jsonify({"status": "success", "message": "Druck erfolgreich gestartet"})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler: {str(e)}"})

# Route: Druck stoppen
@app.route("/stop", methods=["POST"])
def stop_print():
    try:
        url = f"{OCTOPRINT_URL}/api/job"  # OctoPrint-Job-API
        headers = {"X-Api-Key": API_KEY}
        data = {"command": "cancel"}  # Der Befehl zum Stoppen eines Drucks
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 204:  # HTTP 204 No Content bedeutet Erfolg
            return jsonify({"status": "success", "message": "Druck erfolgreich gestoppt"})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler: {str(e)}"})

#Route: Druck pausieren
@app.route("/pause", methods=["POST"])
def pause_print():
    try:
        url = f"{OCTOPRINT_URL}/api/job"
        headers = {"X-Api-Key": API_KEY}
        data = {"command": "pause", "action": "toggle"}  # "toggle" wechselt zwischen Pause/Fortsetzen
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 204:
            return jsonify({"status": "success", "message": "Druck pausiert/fortgesetzt"})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fehler: {str(e)}"})
    
#Druckstatus abrufen    
@app.route("/status", methods=["GET"])
def get_status():
    try:
        url = f"{OCTOPRINT_URL}/api/job"
        headers = {"X-Api-Key": API_KEY}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # Extrahiere den Fortschritt und die verbleibende Zeit
            status = {
                "progress": data.get("progress", {}).get("completion", 0),
                "time_left": data.get("progress", {}).get("printTimeLeft", None),
                "state": data.get("state", "Unbekannt")
            }
            return jsonify({"status": "success", "data": status})
        else:
            return jsonify({"status": "error", "message": response.json()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
