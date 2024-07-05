import os
import time
import requests
import re
from urllib.parse import unquote
from flask import Flask, jsonify, request

app = Flask(__name__)


def get_coordinates_from_short_url(short_url):
    try:
        time.sleep(5)
        response = requests.head(short_url, allow_redirects=True)
        time.sleep(2)
        long_url = response.url
        print(f"Resolved long URL from short URL: {long_url}")
        match = re.search(r"\/(-?\d+\.\d+),\+(-?\d+\.\d+)", unquote(long_url))
        if match:
            lat = float(match.group(1))
            lon = float(match.group(2))
            print(f"Extracted coordinates from long URL: {lat}, {lon}")
            return lat, lon
        else:
            print("Coordinates not found in the long URL.")
            return None, None
    except Exception as e:
        print(f"Error resolving short URL: {e}")
        return None, None


def get_address_from_google_maps_url(long_url):
    try:
        if "https://www.google.com/maps/place/" in long_url:
            address_part = long_url.split("https://www.google.com/maps/place/")[
                1
            ].split("/")[0]
            address = unquote(address_part).replace("+", " ")
            print(f"Extracted address: {address}")
            return address
        else:
            print("Address not found in the URL.")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_coordinates(address):
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    endpoint = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    try:
        print(f"Geocoding request URL: {endpoint}")
        response = requests.get(endpoint)
        data = response.json()

        print(f"Geocoding response: {data}")

        if response.status_code == 200 and data.get("status") == "OK":
            location = data["results"][0]["geometry"]["location"]
            lat = location["lat"]
            lng = location["lng"]
            return lat, lng
        else:
            print(
                f"Geocoding failed with status: {data.get('status')}, error_message: {data.get('error_message')}"
            )
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
        print(f"Resolved long URL: {long_url}")
        address = get_address_from_google_maps_url(long_url)

        if address:
            latitude, longitude = get_coordinates(address)
            if latitude is not None and longitude is not None:
                google_maps_link = (
                    f"https://www.google.com/maps?q={latitude},{longitude}"
                )
                return (
                    jsonify(
                        {
                            "co-ordinates": {
                                "latitude": latitude,
                                "longitude": longitude,
                            },
                            "google_maps_link": google_maps_link,
                        }
                    ),
                    200,
                )
            else:
                print(f"Geocoding failed for extracted address: {address}")

        latitude, longitude = get_coordinates_from_short_url(location_link)
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
                jsonify({"error": "Failed to extract coordinates from URL."}),
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
