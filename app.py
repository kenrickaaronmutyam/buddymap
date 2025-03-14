from flask import Flask, render_template_string, request, jsonify
from opencage.geocoder import OpenCageGeocode
import requests

app = Flask(__name__)

# API Keys (replace with your actual keys)
GOOGLE_API_KEY = 'AIzaSyB-aUav8DSYUJPvKIFJvdjAYR6iyWNAJ1g'
OPENCAGE_API_KEY = '4312606e87464e21be017bdd3876e69f'

geocoder = OpenCageGeocode(OPENCAGE_API_KEY)

HTML = """
<!doctype html>
<html>
<head>
    <title>Find Nearby Places</title>
</head>
<body>
    <h2>Get Current Location and Nearby Places</h2>
    <button onclick="getLocation()">Get Location</button>
    <p id="result"></p>
    <h3>Nearby Places:</h3>
    <ul id="places"></ul>

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