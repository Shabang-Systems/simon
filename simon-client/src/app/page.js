import Link from "next/link";

export default async function Home() {
    return (
        <>
            <div>Hewo hi so this page should in theory contain your recent notes, etc. But I don't want to build a notes app right now because that's like lame.</div>
            <div>So for now you get the quick capture screen</div>
            <Link href="/jot">Click here.</Link>
        </>
    );
}
