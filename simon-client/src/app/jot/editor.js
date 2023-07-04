'use client';

import { useState, useEffect } from "react";
import dynamic from 'next/dynamic';
const ReactQuill = dynamic(() => import("react-quill"), { ssr: false });
import 'react-quill/dist/quill.bubble.css';
import "./editor.css";
import strings from "@lib/strings.json";

export default function Editor() {
    const [title, setTitle] = useState('');
    const [value, setValue] = useState('');

    // useEffect(() => {
    //     console.log(value);
    // }, [value]);

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
                value={value}
                onChange={setValue}
                placeholder={strings.jot_editor_placeholder}
                theme="bubble"/>
        </div>
    );
}
