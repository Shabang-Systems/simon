/* Gets a route to the server
 * Basically by appending /route to the base
 * but smartly using the URL libarry.
 */
function getRoute(route) {
    return new URL(`../${route}`, process.env.SERVER_URL)
}

export async function startSession() {
    let base = getRoute("start")
    base.searchParams.append('providers', 'map')

    const res = await fetch(base.toString(), {
        method: "POST",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({google_maps_key: process.env.GOOGLE_MAPS_KEY})
    });

    return (await res.json()).session_id;
}

