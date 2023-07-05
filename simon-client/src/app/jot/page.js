import Editor from "./editor.js";
import "./page.css";

import { startSession } from "@lib/utils.js";

export default async function Jot() {
    return (
        <Editor session={await startSession()}/>
    );
}
