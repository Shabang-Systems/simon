'use client';

import { useState, useEffect, useRef } from "react";
import dynamic from 'next/dynamic';
const ReactQuill = dynamic(() => import("react-quill"), { ssr: false });
import 'react-quill/dist/quill.bubble.css';
import "./editor.css";
import strings from "@lib/strings.json";

/* locations(substring, string)
 * calculate all instances of "substring" in "string"
 * if there are overlapping substrings, return 
 * discrete chunks in those options instead of
 * each individual overlap
 */
function locations(substring, string) {
    let substring_len = substring.length;
    let results = [];
    for (let i=0; i<string.length-substring_len+1; i++) {
        if (string.slice(i, i+substring_len) == substring) {
            results.push(i);
            i = i+substring_len-1;
        }
    }

    return results;
}

export default function Editor() {
    const [title, setTitle] = useState('');
    const [html, setHTML] = useState('');
    const [text, setText] = useState('');
    const editorRef = useRef(null);

    useEffect(() => {
        // calculate where linebreaks are, if the text has actual content
        // we place one chunk at the beginning 
        let linebreak_locations = locations("\n\n", text);
        linebreak_locations = [0, ...linebreak_locations];

        // create the chunks based on where double newlines are
        let raw_chunks = text.split("\n\n");
        let html_chunks = html.split("<br>");

        // and gather top locations for each of the chunks
        if (editorRef.current) {
            let tops = linebreak_locations.map(i => editorRef.current.getBounds(i+1).top);
            console.log(raw_chunks, tops);
        }
    }, [text, html]);

    return (
        <div id="editor-container">
            <input id="editor-title"
                   placeholder={strings.jot_editor_title}
                   autoFocus={true}
                   value={title}
                   onChange={(e) => setTitle(e.value)}
                   type="text"></input>
            <ReactQuill
                id="editor-text"
                value={html}
                onChange={(content, _1, _2, editor) => {
                    setHTML(content);
                    setText(editor.getText().trim());
                    editorRef.current = editor;
                    /*  */
                    /* let sel = editor.getSelection(); */
                    /* let line_position = editor.getBounds(sel.index).top; */
                    /* console.log(diff); */
                    /* console.log(content); */
                    // TODO this is the position we need
                }}
                placeholder={strings.jot_editor_placeholder}
                theme="bubble"/>
            {/* The following is a focus clearfix so users can click */}
            {/* anywhere to get focus */}
            <div style={{height: "110%", cursor: "text"}}
                 onClick={()=>
                     document.getElementsByClassName("ql-editor")[0].focus()
                 }>&nbsp;</div>
        </div>
    );
}
