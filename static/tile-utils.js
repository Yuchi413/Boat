export function latlon_to_tile(lat, lon, zoom) {
    const x = Math.floor((lon + 180) / 360 * Math.pow(2, zoom));
    const y = Math.floor(
        (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom)
    );
    return { x, y };
}

export function getTilesInRange(minLat, maxLat, minLon, maxLon, zoom = 16) {
    const topLeft = latlon_to_tile(maxLat, minLon, zoom);
    const bottomRight = latlon_to_tile(minLat, maxLon, zoom);
    const tiles = [];

    for (let x = topLeft.x; x <= bottomRight.x; x++) {
        for (let y = topLeft.y; y <= bottomRight.y; y++) {
            tiles.push({ z: zoom, x, y });
        }
    }
    return tiles;
}
