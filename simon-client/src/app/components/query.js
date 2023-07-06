"use client";

import "./query.css";
import { useEffect, useState } from "react";
import { chat } from "@lib/utils";
import strings from "@lib/strings.json";

import { TextChunk } from "./widgets/base.js";

export function QueryLoading() {
    return (
        <div className="qm-load">
            <div className="lds-facebook"><div></div><div></div><div></div></div>
            <span>{strings.query_postulating}</span>
        </div>
    );
}

function Widget({res}) {
    let [widget, setWidget] = useState(<></>);

    useEffect(() => {
        // serialize special responses
        if (res.response.widget == "TextChunk") {
            setWidget(<TextChunk payload={res.response.payload}/>);
        } else {
            // TODO give up other widgets are needed
            setWidget(<div style={{whiteSpace: "pre-line"}}>{res.response.raw}</div>);
        }
    }, [res]);

    return widget;
}

export default function QueryModal({text, session}) {
    let [res, setRes] = useState({response: {}});
    let [ready, setReady] = useState(false);

    useEffect(() => {
        setReady(false);
        chat(text, session).then((res) => {
            setRes(res);
            setReady(true);
        });
    }, [text, session]);

    return (
        <div className="queryModal">
            <span className="qm-query">{text}</span>
            <div className="qm-response">
                <div className="qm-response-body">
                    <Widget res={res}/>
                </div>
            </div>
        </div>
    );
}
