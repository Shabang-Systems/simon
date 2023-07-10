/* Gets a route to the server
 * Basically by appending /route to the base
 * but smartly using the URL libarry.
 */

"use server"

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
        body: JSON.stringify({google_maps_key: process.env.GOOGLE_MAPS_KEY}),
    });

    return (await res.json()).session_id;
}

export async function brainstorm(text, session) {
    let base = getRoute("brainstorm")
    base.searchParams.append('q', text)
    base.searchParams.append('session_id', session)

    const res = await fetch(base.toString(), {
        method: "GET",
    });

    return (await res.json());
}

export async function chat(text, session) {
    console.log("I HAVE BENE CALLED");
    let base = getRoute("chat")
    base.searchParams.append('q', text)
    base.searchParams.append('session_id', session)

    const res = await fetch(base.toString(), {
        method: "GET",
    });

    return (await res.json());
}
