// Script to clean up auto-configured inboxes and keep only Executive AI Assistant and Multi-Agent
// Run this in your browser console while on the Agent Inbox page (http://localhost:3000)

console.log("🧹 Starting inbox cleanup...");

// Clear existing inboxes
localStorage.removeItem("inbox:agent_inboxes");
localStorage.removeItem("inbox:id_backfill_completed");

console.log("✅ Cleared auto-configured inboxes");

// Set up clean inbox configuration with only Executive AI Assistant and Multi-Agent
const cleanInboxes = [
  {
    id: "executive-ai-assistant",
    name: "Executive AI Assistant",
    description: "AI email assistant for processing emails and scheduling",
    deploymentUrl: "http://localhost:2024",
    graphId: "executive_main",
    selected: true
  },
  {
    id: "multi-agent",
    name: "Multi-Agent",
    description: "Multi-agent supervisor system",
    deploymentUrl: "http://localhost:2024",
    graphId: "agent",
    selected: false
  }
];

// Save clean configuration
localStorage.setItem("inbox:agent_inboxes", JSON.stringify(cleanInboxes));

console.log("✅ Set up clean inbox configuration:");
console.log(cleanInboxes);

console.log("🎉 Inbox cleanup complete! Refresh the page to see changes.");

// Optional: Automatically refresh the page
if (confirm("Refresh the page to see the cleaned up inboxes?")) {
  window.location.reload();
}
