import dynamic from "next/dynamic";

const Alignment = dynamic(() => import("../components/alignments"), { ssr: false });

export default Alignment;
