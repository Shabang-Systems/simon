import Editor from "./editor";
import strings from "@lib/strings.json";

import "./page.css";

// a server action to render a specific
// chunk that got updated
async function render(e) {
    "use server";
    console.log(e);
}

export default async function Jot() {
    return (
        <div id="jot">
            <div id="main"><Editor render={render}/></div>
            <div id="rightbar"> </div>
        </div>

    );
}
