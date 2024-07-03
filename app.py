import os
import requests
import re
from urllib.parse import unquote
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_address_from_google_maps_url(long_url):
    try:
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", unquote(long_url))
        if match:
            coordinates = match.group(0)
            address = (
                long_url.split("/@")[0]
                .replace("https://www.google.com/maps/place/", "")
                .replace(",", " ")
                .replace("+", " ")
            )
            return address
        else:
            print("Coordinates not found in the URL.")
            return None
    except Exception as e:
        print(f"Error extracting address from URL: {e}")
        return None


def get_coordinates(address):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    endpoint = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    try:
        response = requests.get(endpoint)
        data = response.json()

        if response.status_code == 200 and data.get("status") == "OK":
            location = data["results"][0]["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]
            return lat, lng
        else:
            print(f"Geocoding failed with status: {data.get('status')}")
            return None, None
    except Exception as e:
        print(f"Error geocoding: {e}")
        return None, None


@app.route("/api/location", methods=["GET"])
def get_google_maps_link():
    location_link = request.args.get("location_link")

    if not location_link:
        return jsonify({"error": "No location link found in request parameters."}), 400

    try:
        response = requests.head(location_link, allow_redirects=True)
        long_url = response.url
        address = get_address_from_google_maps_url(long_url)

        if not address:
            return jsonify({"error": "Failed to extract address from URL."}), 400

        latitude, longitude = get_coordinates(address)

        if latitude is not None and longitude is not None:
            google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            return (
                jsonify(
                    {
                        "co-ordinates": {"latitude": latitude, "longitude": longitude},
                        "google_maps_link": google_maps_link,
                    }
                ),
                200,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to retrieve coordinates for the address extracted from URL."
                    }
                ),
                400,
            )
    except Exception as e:
        print(f"Error processing request: {e}")
        return (
            jsonify({"error": "An error occurred while processing the request."}),
            500,
        )


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
