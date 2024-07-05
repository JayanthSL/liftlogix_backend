import os
from dotenv import load_dotenv
from flask import Flask, json, jsonify, request

from google.cloud import firestore

app = Flask(__name__)

load_dotenv()

service_account_key = os.getenv("FIREBASE_SERVICE_ACCOUNT")
db = firestore.Client.from_service_account_json(service_account_key)


@app.route("/api/coordinates", methods=["GET"])
def get_coordinates_for_orders():
    try:
        phone_number = request.args.get("phone_number")
        final = "+" + phone_number.replace(" ", "")
        print(final)
        if not phone_number:
            return jsonify({"error": "Phone number is required"}), 400

        location_ref = db.collection("location").document(final)
        print(location_ref)
        orders_ref = location_ref.collection("orders").get()

        coordinates_array = []
        for order in orders_ref:
            coordinates = order.to_dict().get("coordinates")
            if coordinates:
                coordinates_array.append(coordinates)

        return jsonify(coordinates_array)

    except Exception as e:
        return jsonify({"error": f"Error retrieving coordinates for orders: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
