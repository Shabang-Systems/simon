import Editor from "./editor";
import strings from "@lib/strings.json";

import "./page.css";

export default async function Jot() {
    return (
        <div id="jot">
            <div id="main"><Editor/></div>
            <div id="rightbar"> </div>
        </div>

    );
}
