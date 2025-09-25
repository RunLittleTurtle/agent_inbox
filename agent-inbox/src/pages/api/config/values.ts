import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';

function getCurrentEnvValues() {
  try {
    const projectRoot = process.cwd().split('/agent-inbox')[0];
    const envPath = path.join(projectRoot, '.env');

    // Load environment variables from .env file
    config({ path: envPath });

    return process.env;
  } catch (error) {
    console.error('Error reading .env file:', error);
    return {};
  }
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const { agentId } = req.query;

    try {
      // Get current environment variable values
      const envValues = getCurrentEnvValues();

      // For now, we'll return env values for all agents
      // TODO: Implement agent-specific config value retrieval
      res.status(200).json({
        success: true,
        values: envValues,
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