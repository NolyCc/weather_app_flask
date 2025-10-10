
(function () {
  const useGeo = document.getElementById("use_geo");
  const lat = document.getElementById("lat");
  const lon = document.getElementById("lon");
  const form = document.getElementById("weather-form");

  if (!useGeo || !lat || !lon) return;

  useGeo.addEventListener("change", () => {
    if (useGeo.checked && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          lat.value = pos.coords.latitude;
          lon.value = pos.coords.longitude;
        },
        (err) => {
          alert("Failed to get location: " + err.message);
          useGeo.checked = false;
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
      );
    } else {
      lat.value = "";
      lon.value = "";
    }
  });
})();
