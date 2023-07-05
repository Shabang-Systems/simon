import "./query.css";
import { Suspense } from "react";
import { chat } from "@lib/utils";
import strings from "@lib/strings.json";

import { TextChunk } from "./widgets/base.js";

export async function QueryLoading() {
    return (
        <>
            <div className="qm-load">
                <div className="lds-facebook"><div></div><div></div><div></div></div>
                <span>{strings.query_postulating}</span>
            </div>
        </>
    );
}

export async function QueryResponse({text, session}) {
    let res = await chat(text, session);
    let widget;

    // serialize special responses
    if (res.response.widget == "TextChunk") {
        widget = <TextChunk payload={res.response.payload}/>;
    } else {
        // TODO give up other widgets are needed
        widget = <div style={{whiteSpace: "pre-line"}}>{res.response.raw}</div>;
    }

    return (
        <div className="qm-response-body">
            {widget}
        </div>
    );
}

export default async function QueryModal({text, session}) {
    return (
        <div className="queryModal">
            <span className="qm-query">{text}</span>
            <div className="qm-response">
                <Suspense fallback={<QueryLoading/>}>
                    <QueryResponse text={text} session={session}/>
                </Suspense>
            </div>
        </div>
    );
}

