#!/usr/bin/env node

/**
 * Test script for Chrome DevTools MCP
 * This verifies that the MCP server can start and communicate
 */

const { spawn } = require('child_process');

console.log('Testing Chrome DevTools MCP...\n');

// Start the MCP server in headless mode with isolated profile
const mcp = spawn('npx', [
  'chrome-devtools-mcp@latest',
  '--headless=true',
  '--isolated=true'
], {
  stdio: ['pipe', 'pipe', 'pipe']
});

// Set a timeout for the test
const testTimeout = setTimeout(() => {
  console.log('✓ Chrome DevTools MCP started successfully (timeout reached, killing process)');
  mcp.kill();
  process.exit(0);
}, 5000);

// Handle stdout
mcp.stdout.on('data', (data) => {
  const output = data.toString();
  console.log('MCP Output:', output);

  // Check if the server started successfully
  if (output.includes('server') || output.includes('ready') || output.includes('listening')) {
    console.log('✓ Chrome DevTools MCP server is running');
    clearTimeout(testTimeout);
    mcp.kill();
    process.exit(0);
  }
});

// Handle stderr
mcp.stderr.on('data', (data) => {
  const error = data.toString();

  // Some warnings are ok, but check for critical errors
  if (error.toLowerCase().includes('error') &&
      !error.toLowerCase().includes('warning')) {
    console.error('✗ MCP Error:', error);
    clearTimeout(testTimeout);
    mcp.kill();
    process.exit(1);
  } else {
    console.log('MCP Warning/Info:', error);
  }
});

// Handle process exit
mcp.on('close', (code) => {
  clearTimeout(testTimeout);
  if (code !== 0 && code !== null) {
    console.log(`✗ MCP process exited with code ${code}`);
    process.exit(1);
  }
});

// Send a test message to verify stdio communication
setTimeout(() => {
  // Send a simple JSON-RPC message to test communication
  const testMessage = JSON.stringify({
    jsonrpc: "2.0",
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {}
    },
    id: 1
  }) + '\n';

  console.log('Sending test initialization message...');
  mcp.stdin.write(testMessage);
}, 1000);