import { defineModule, defineModuleRoute } from "@ocelescope/core";
import { SquareCenterlineDashedVertical } from "lucide-react";
import Alignments from "./routes/alignments";

export const alignmentspage = defineModuleRoute({
  component: Alignments,
  label: "example",
  name: "example",
  requiresOcel: true,
});

export default defineModule({
  name: "caseCentricAlignments",
  label: "Case-Centric Alignments",
  description: "case-centric Alignments",
  authors: [{ name: "Uy Sa Huynh" }],
  icon: SquareCenterlineDashedVertical,
  routes: [alignmentspage],
});
