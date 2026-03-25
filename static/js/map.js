// This file requires Leaflet.js to be loaded in the HTML
document.addEventListener('DOMContentLoaded', () => {
    
    // Only initialize the map if the #map container exists on the page
    const mapContainer = document.getElementById('map');
    
    if (mapContainer) {
        // Initialize map centered on Durban, South Africa
        const map = L.map('map').setView([-29.8587, 31.0218], 12);

        // Add free OpenStreetMap tiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Define a custom icon for the campus shuttles
        const busIcon = L.icon({
            iconUrl: 'https://cdn-icons-png.flaticon.com/512/3448/3448339.png', // Example open-source icon
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32]
        });

        // Simulate real-time shuttle locations [cite: 28]
        // In a real app, you would fetch this data from your Flask backend using fetch('/api/shuttles')
        const shuttles = [
            { id: 'BUS 03', lat: -29.8500, lng: 31.0100, status: 'On Time', seats: '20/65' },
            { id: 'BUS 79', lat: -29.8650, lng: 30.9900, status: 'Delayed', seats: 'Full' }
        ];

        // Add markers for each shuttle
        shuttles.forEach(shuttle => {
            let marker = L.marker([shuttle.lat, shuttle.lng], {icon: busIcon}).addTo(map);
            
            // Format the popup content
            let popupContent = `
                <strong>${shuttle.id}</strong><br>
                Status: ${shuttle.status}<br>
                Seats: ${shuttle.seats}
            `;
            marker.bindPopup(popupContent);
        });

        // Optional: If user allows location, show their position to help them find nearby rides
        map.locate({setView: true, maxZoom: 14});
        
        map.on('locationfound', (e) => {
            L.circleMarker(e.latlng, {
                radius: 8,
                fillColor: "#0066cc",
                color: "#fff",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.8
            }).addTo(map).bindPopup("You are here").openPopup();
        });
    }
});