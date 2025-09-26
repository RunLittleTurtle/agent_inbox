import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';

function getCurrentEnvValues() {
  try {
    // Get the project root - go up from agent-inbox directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const envPath = path.join(projectRoot, '.env');

    // Load environment variables from .env file
    config({ path: envPath });

    return process.env;
  } catch (error) {
    console.error('Error reading .env file:', error);
    return {};
  }
}

function getPythonConfigValues(agentId: string | string[] | undefined) {
  try {
    if (agentId === '_react_agent_mcp_template') {
      // Read values from the template's config.py
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, 'src/_react_agent_mcp_template/config.py');

      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');

        // Extract LLM_CONFIG values
        const modelMatch = content.match(/"model":\s*"([^"]+)"/);
        const tempMatch = content.match(/"temperature":\s*([\d.]+)/);
        const maxTokensMatch = content.match(/"max_tokens":\s*([\d]+)/);
        const streamingMatch = content.match(/"streaming":\s*(True|False)/);

        // Extract agent identity values
        const agentNameMatch = content.match(/AGENT_NAME\s*=\s*"([^"]+)"/);
        const displayNameMatch = content.match(/AGENT_DISPLAY_NAME\s*=\s*"([^"]+)"/);
        const descriptionMatch = content.match(/AGENT_DESCRIPTION\s*=\s*"([^"]+)"/);
        const mcpServiceMatch = content.match(/MCP_SERVICE\s*=\s*"([^"]+)"/);

        return {
          llm: {
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.2,
            max_tokens: maxTokensMatch ? parseInt(maxTokensMatch[1]) : 2000,
            streaming: streamingMatch?.[1] === 'True'
          },
          agent_identity: {
            agent_name: agentNameMatch?.[1] || '{AGENT_NAME}',
            agent_display_name: displayNameMatch?.[1] || '{AGENT_DISPLAY_NAME}',
            agent_description: descriptionMatch?.[1] || '{AGENT_DESCRIPTION}',
            mcp_service: mcpServiceMatch?.[1] || '{MCP_SERVICE}'
          }
        };
      }
    }
  } catch (error) {
    console.error('Error reading Python config values:', error);
  }

  return {};
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const { agentId } = req.query;

    try {
      // Get current environment variable values
      const envValues = getCurrentEnvValues();

      // Get Python config values if applicable
      const pythonValues = getPythonConfigValues(agentId);

      // Merge the values - env values are flat, Python values are nested
      const mergedValues = {
        ...envValues,
        ...pythonValues
      };

      res.status(200).json({
        success: true,
        values: mergedValues,
        agentId,
      });
    } catch (error) {
      console.error('Error getting config values:', error);
      res.status(500).json({
        success: false,
        error: 'Failed to retrieve configuration values',
      });
    }
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}