import { brainstorm } from "@lib/utils.js";
import "./response.css";

export function LoadingResponse() {
    return (<div classname="simon-brainstorm-loading">
                nana goon
            </div>);
}

export default async function Response({text, session}) {
    let thoughts = await brainstorm(text, session);

    return (
        <div className="simon-brainstorm">
            <ul className="simon-brainstorm-question-list">
                {thoughts.response.questions.map(i => (
                    <li className="simon-brainstorm-question">{i}</li>
                ))}
            </ul>
        </div>
    );
}
