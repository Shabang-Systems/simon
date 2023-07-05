// UI
import Editor from "@components/editor.js";
import QueryModal from "@components/query.js";

// styles
import "./page.css";

// tools
import { startSession } from "@lib/utils.js";

// react stuff
import { Suspense } from 'react';

// TODO this should eventually be something
// in the user's cookies or something client side
// so that the session can have actual auth

let session = await startSession();

export default async function Jot(props) {
    let query = props.searchParams.q;

    return (
        <>
            <Editor session={session}/>
            {query ? (<QueryModal text={query}
                                  session={session}/>) : (<></>)}
        </>
    );
}
