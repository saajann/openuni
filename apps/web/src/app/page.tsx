import type { Metadata } from "next";

import { ChatWorkspace } from "@/components/chat-workspace";

export const metadata: Metadata = {
  // The root layout's title template does not apply to the index route, so
  // set the full title explicitly here.
  title: { absolute: "Ask | OpenUni" },
  description:
    "Ask a question about your university and get an answer grounded in official documents, with citations.",
};

export default function HomePage() {
  return <ChatWorkspace />;
}
