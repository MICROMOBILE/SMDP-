from flask import Flask, request, jsonify, send_file
import qrcode, uuid, io
from profile_codec import encode_profile

app = Flask(__name__)

profiles = {}

@app.route("/create-esim", methods=["POST"])
def create_esim():
    eid = str(uuid.uuid4())[:12]
    iccid = "8901234567890123456"
    imsi = "310150123456789"
    msisdn = "+15555550123"

    profile = {
        "iccid": iccid,
        "imsi": imsi,
        "msisdn": msisdn,
        "carrier": "Micro Mobile",
        "country": "CA",
        "activationCode": f"micro-{eid}"
    }

    profiles[eid] = profile
    return jsonify({"eid": eid, "activationCode": profile["activationCode"], "qr": f"/qr/{eid}"})

@app.route("/qr/<eid>")
def generate_qr(eid):
    profile = profiles.get(eid)
    if not profile:
        return "Not found", 404
    url = request.host_url.strip("/") + "/esim"
    qr_string = f"LPA:1${url}${profile['activationCode']}"
    img = qrcode.make(qr_string)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/esim", methods=["POST"])
def handle_esim():
    data = request.json
    activation_code = data.get("activationCode")
    for eid, profile in profiles.items():
        if profile["activationCode"] == activation_code:
            profile["status"] = "downloaded"
            return jsonify({
                "smdpAddress": request.host_url.strip("/") + "/getBoundProfilePackage",
                "eid": eid
            })
    return jsonify({"error": "activationCode invalid"}), 404

@app.route("/getBoundProfilePackage", methods=["POST"])
def send_profile():
    data = request.json
    eid = data.get("eid")
    profile = profiles.get(eid)
    if not profile:
        return "Profile not found", 404

    encoded = encode_profile(profile)
    return send_file(
        io.BytesIO(encoded),
        download_name="profile.der",
        mimetype="application/octet-stream",
        as_attachment=True
    )

if __name__ == "__main__":
    app.run(port=5000, ssl_context=("cert.pem", "key.pem"))
