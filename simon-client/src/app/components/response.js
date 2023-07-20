"use client";

import { brainstorm } from "@lib/utils.js";
import "./response.css";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Response({text, session, onQuery}) {
    let [questions, setQuestions] = useState([]);
    let [goal, setGoal] = useState("");
    let [ready, setReady] = useState(false);

    let router = useRouter();


    useEffect(() => {
        brainstorm(text, session).then((thoughts) => {
            setReady(true);
            setQuestions(thoughts.response.comments.map(i => i.comment));
            setGoal(thoughts.response.gap);
        });
    }, [text]);

    return (
        <div className="simon-brainstorm">
            <span className="simon-brainstorm-goal">{goal}</span>
            {ready?
             <ul className="simon-brainstorm-question-list">
                 {questions.map((i, indx) => (
                     <li key={indx} className="simon-brainstorm-question"
                         onClick={() => {
                             if (onQuery) onQuery(goal+' ' + i);
                         }}>{i}</li>
                 ))}
             </ul>: <div>maaah</div>}
        </div>
    );
}
