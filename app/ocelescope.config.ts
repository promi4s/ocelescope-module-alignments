import type { OcelescopeConfig } from "@ocelescope/core";
import management from "@ocelescope/management";
import caseCentricAlignmentsModule from "@instance/case-centric-alignments";

// `pnpm run add:frontend` adds local frontend modules here.
export default {
	modules: [management, caseCentricAlignmentsModule],
} satisfies OcelescopeConfig;
