from flask import Flask, render_template_string, request, jsonify
from opencage.geocoder import OpenCageGeocode
import os
import requests

app = Flask(__name__)

# API Keys (replace with your actual keys)
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
OPENCAGE_API_KEY = os.getenv('OPENCAGE_API_KEY')

geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

HTML = """
```html
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>BuddyMap - Find Nearby Places</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
        }

        h2 {
            color: #2c3e50;
        }

        button {
            background-color: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s ease;
            margin-top: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        button:hover {
            background-color: #2980b9;
        }

        #result {
            margin-top: 10px;
            font-size: 18px;
            font-weight: bold;
            color: #27ae60;
        }

        h3 {
            color: #2c3e50;
            margin-top: 20px;
        }

        ul {
            list-style: none;
            padding: 0;
            width: 100%;
            max-width: 400px;
        }

        li {
            background-color: #ecf0f1;
            margin-bottom: 10px;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.3s ease;
        }

        li:hover {
            background-color: #d0e6f1;
        }

        a {
            text-decoration: none;
            color: #3498db;
            font-weight: bold;
            transition: color 0.2s ease;
        }

        a:hover {
            color: #2980b9;
        }

        @media (max-width: 480px) {
            button {
                width: 100%;
            }

            li {
                font-size: 14px;
                padding: 12px;
            }
        }
    </style>
</head>
<body>
    <h2>BuddyMap - Find Nearby Places</h2>
    <button onclick="getLocation()">Get Location</button>
    <p id="result"></p>
    <h3>Nearby Places:</h3>
    <ul id="places">
        <li>Starbucks <a href="https://www.google.com/maps/search/?api=1&query=Starbucks" target="_blank">View</a></li>
        <li>Pizza Hut <a href="https://www.google.com/maps/search/?api=1&query=Pizza+Hut" target="_blank">View</a></li>
        <li>Book Store <a href="https://www.google.com/maps/search/?api=1&query=Book+Store" target="_blank">View</a></li>
    </ul>
<script>
        function getLocation() {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(showPosition, showError);
            } else {
                document.getElementById("result").innerHTML = "Geolocation is not supported by this browser.";
            }
        }

        function showPosition(position) {
            fetch('/location', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById("result").innerHTML = 
                    `Latitude: ${data.latitude}, Longitude: ${data.longitude}<br>
                    Location: ${data.location}`;

                // Fetch nearby places
                fetch('/places', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        latitude: data.latitude,
                        longitude: data.longitude
                    })
                })
                .then(response => response.json())
                .then(data => {
                    const placesList = document.getElementById("places");
                    placesList.innerHTML = "";
                    data.forEach(place => {
                        const li = document.createElement("li");
                        li.textContent = place;
                        placesList.appendChild(li);
                    });
                });
            });
        }

        function showError(error) {
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    alert("User denied the request for Geolocation.");
                    break;
                case error.POSITION_UNAVAILABLE:
                    alert("Location information is unavailable.");
                    break;
                case error.TIMEOUT:
                    alert("The request to get user location timed out.");
                    break;
                case error.UNKNOWN_ERROR:
                    alert("An unknown error occurred.");
                    break;
            }
        }
    </script>
</body>
</html>
```
"""

# Flask route to serve the HTML page
@app.route('/')
def index():
    return render_template_string(HTML)

# Route to get the current location using GPS
@app.route('/location', methods=['POST'])
def location():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    # Reverse geocode using OpenCage
    result = geocoder.reverse_geocode(lat, lon)
    if result and len(result):
        location = result[0]['formatted']
        return jsonify({'latitude': lat, 'longitude': lon, 'location': location})
    else:
        return jsonify({'error': 'Failed to get location details'}), 400

# Route to get nearby places using Google Places API
@app.route('/places', methods=['POST'])
def places():
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    place_types = ["restaurant", "supermarket", "book_store", "grocery_or_supermarket", "beauty_salon", "shopping_mall"]
    places_list = []

    for place_type in place_types:
        url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lon}&radius=1500&type={place_type}&key={GOOGLE_API_KEY}"
        response = requests.get(url)
        results = response.json().get('results', [])

        for place in results:
            name = place.get('name')
            if name:
                places_list.append(f"{place_type.replace('_', ' ').title()}: {name}")

    return jsonify(places_list)

if __name__ == '__main__':
    app.run(debug=True)