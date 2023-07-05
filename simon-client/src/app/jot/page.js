// UI
import Editor from "./editor.js";

// styles
import "./page.css";

// tools
import { startSession } from "@lib/utils.js";

// react stuff
import { Suspense } from 'react';

// TODO this should eventually be something
// in the user's cookies or something client side
// so that the session can have actual auth

export default async function Jot() {

    // async function update(res) {
    //     // TODO this is reaaaly jank but it seems to work
    //     // basically on every update, the client calls
    //     // refresh and then the server refreshes.

    //     // this is only because
    //     // like each client write requires a whole server
    //     // call and a long wait time and can't just be reflected
    //     // client side. 
        
    //     'use server'
    //     chunks = res.filter((i)=>i.text != "");
    // }
    // console.log(chunks);

    return (
        <Editor session={await startSession()}/>
    );
}
