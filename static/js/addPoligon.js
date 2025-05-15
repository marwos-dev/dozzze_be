document.addEventListener("DOMContentLoaded", function () {
    const zoneSelect = document.querySelector("#id_zone");
    const geodjangoWidget = window.geodjango_location;
    const map = geodjangoWidget.map;

    zoneSelect.addEventListener("change", function () {
        const zoneId = this.value;
        if (!zoneId) return;

        fetch(`/api/zones/${zoneId}/polygon`, {
            credentials: "same-origin",
        })
            .then((response) => {
                if (!response.ok) throw new Error("Network response was not ok");
                return response.json();
            })
            .then((data) => {
                if (data.coordinates) {
                    const geojson = JSON.parse(data.coordinates);
                    const polygon = new ol.format.GeoJSON().readFeature(geojson, {
                        featureProjection: "EPSG:3857",
                    });

                    if (window.zoneLayer) {
                        map.removeLayer(window.zoneLayer);
                    }

                    window.zoneLayer = new ol.layer.Vector({
                        source: new ol.source.Vector({
                            features: [polygon],
                        }),
                        style: new ol.style.Style({
                            stroke: new ol.style.Stroke({
                                color: "#f00",
                                width: 2,
                            }),
                            fill: new ol.style.Fill({
                                color: "rgba(255, 0, 0, 0.1)",
                            }),
                        }),
                    });

                    map.addLayer(window.zoneLayer);

                    // Centrar el mapa en el polígono
                    const extent = window.zoneLayer.getSource().getExtent();
                    map.getView().fit(extent, { padding: [20, 20, 20, 20] });
                }
            })
            .catch((error) => {
                console.error("Error al obtener el polígono:", error);
            });
    });
});
