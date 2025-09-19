// Automated cleanup script that can be run directly to clean localStorage
// This version clears localStorage and sets up the clean configuration

(function cleanupInboxes() {
  if (typeof window === 'undefined') {
    console.log('❌ This script must be run in a browser environment');
    return;
  }

  console.log("🧹 Starting automated inbox cleanup...");

  // Clear existing inboxes and backfill state
  localStorage.removeItem("inbox:agent_inboxes");
  localStorage.removeItem("inbox:id_backfill_completed");

  // Also clear any other potential inbox-related keys
  const keysToRemove = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && (key.startsWith("inbox:") || key.includes("agent") || key.includes("backfill"))) {
      keysToRemove.push(key);
    }
  }

  keysToRemove.forEach(key => {
    console.log(`🗑️ Removing: ${key}`);
    localStorage.removeItem(key);
  });

  console.log("✅ Cleared all auto-configured data");

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

  // Mark backfill as complete to prevent auto-configuration
  localStorage.setItem("inbox:id_backfill_completed", "true");

  console.log("✅ Set up clean inbox configuration:");
  console.table(cleanInboxes);

  console.log("🎉 Automated cleanup complete!");

  // Show current localStorage state
  console.log("📋 Current localStorage state:");
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith("inbox:")) {
      console.log(`  ${key}: ${localStorage.getItem(key)}`);
    }
  }

  // Auto-refresh if this is being run on the Agent Inbox page
  if (window.location.port === '3000' || window.location.href.includes('agent-inbox')) {
    console.log("🔄 Auto-refreshing page...");
    setTimeout(() => window.location.reload(), 1000);
  }
})();
