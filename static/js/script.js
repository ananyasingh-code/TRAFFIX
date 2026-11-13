
// TRAFFIX Automatic Traffic Updates

async function updateTraffic() {

    try {

        const response = await fetch("/api/traffic");

        if (!response.ok) {
            throw new Error("Unable to fetch traffic data");
        }

        const data = await response.json();

        console.log("Updated Traffic Data:", data);

        // Update all four direction cards
        for (const direction in data.traffic) {

            const card = document.querySelector(
                `[data-direction="${direction}"]`
            );

            if (!card) continue;

            const trafficData = data.traffic[direction];

            card.querySelector(".vehicle-count").textContent =
                trafficData.vehicles;

            card.querySelector(".traffic-density").textContent =
                trafficData.density;

            card.querySelector(".green-time").textContent =
                trafficData.green_time;
        }

        // Update priority direction
        const priorityDirection =
            document.getElementById("priority-direction");

        const priorityDuration =
            document.getElementById("priority-duration");

        if (priorityDirection) {
            priorityDirection.textContent = data.next_green;
        }

        if (priorityDuration) {
            priorityDuration.textContent = data.green_duration;
        }

        // Update User Dashboard traffic information

const userDensity = document.getElementById("user-density");
const userVehicles = document.getElementById("user-vehicles");

if (userDensity) {
    userDensity.textContent =
        data.traffic[data.next_green].density;
}

if (userVehicles) {
    userVehicles.textContent =
        data.traffic[data.next_green].vehicles;
}


        // Update intersection signal indicators
const directions = ["North", "South", "East", "West"];

directions.forEach(direction => {

    const signal = document.querySelector(
        `.${direction.toLowerCase()}-signal`
    );

    if (signal) {
        signal.classList.toggle(
            "active",
            direction === data.next_green
        );
    }

});


    } catch (error) {

        console.error("Traffic Update Error:", error);

    }

}

// Initial update
updateTraffic();

// Automatically update every 5 seconds
setInterval(updateTraffic, 5000);
