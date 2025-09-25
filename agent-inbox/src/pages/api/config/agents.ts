import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface AgentConfig {
  name: string;
  description: string;
  config_type: string;
  config_path: string;
}

interface ConfigSection {
  key: string;
  label: string;
  description: string;
  fields: Array<{
    key: string;
    label: string;
    type: string;
    envVar?: string;
    default?: any;
    description?: string;
    placeholder?: string;
    required?: boolean;
    options?: string[];
    validation?: any;
    note?: string;
    warning?: string;
  }>;
}

interface AgentConfigData {
  CONFIG_INFO: AgentConfig;
  CONFIG_SECTIONS: ConfigSection[];
}

const AGENT_CONFIG_PATHS = [
  'ui_config.py',
  'src/_react_agent_mcp_template/ui_config.py',
  'src/calendar_agent/ui_config.py',
  'src/drive_react_agent/ui_config.py',
  'src/executive-ai-assistant/ui_config_wrapper.py',
  'src/job_search_agent/ui_config.py',
];

function parseConfigFile(filePath: string): AgentConfigData | null {
  try {
    const content = fs.readFileSync(filePath, 'utf8');

    // Extract CONFIG_INFO
    const configInfoMatch = content.match(/CONFIG_INFO\s*=\s*({[\s\S]*?^})/m);
    if (!configInfoMatch) {
      console.error(`No CONFIG_INFO found in ${filePath}`);
      return null;
    }

    // Extract CONFIG_SECTIONS
    const configSectionsMatch = content.match(/CONFIG_SECTIONS\s*=\s*(\[[\s\S]*?^\])/m);
    if (!configSectionsMatch) {
      console.error(`No CONFIG_SECTIONS found in ${filePath}`);
      return null;
    }

    // Convert Python dict syntax to JSON (basic conversion)
    const configInfoStr = configInfoMatch[1]
      .replace(/'/g, '"')
      .replace(/True/g, 'true')
      .replace(/False/g, 'false')
      .replace(/None/g, 'null');

    const configSectionsStr = configSectionsMatch[1]
      .replace(/'/g, '"')
      .replace(/True/g, 'true')
      .replace(/False/g, 'false')
      .replace(/None/g, 'null');

    const configInfo = JSON.parse(configInfoStr);
    const configSections = JSON.parse(configSectionsStr);

    return {
      CONFIG_INFO: configInfo,
      CONFIG_SECTIONS: configSections,
    };
  } catch (error) {
    console.error(`Error parsing ${filePath}:`, error);
    return null;
  }
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    const agents: Array<{
      id: string;
      path: string;
      config: AgentConfigData;
    }> = [];

    const projectRoot = process.cwd().split('/agent-inbox')[0];

    for (const configPath of AGENT_CONFIG_PATHS) {
      const fullPath = path.join(projectRoot, configPath);

      if (fs.existsSync(fullPath)) {
        const config = parseConfigFile(fullPath);
        if (config) {
          // Generate ID from file path
          const id = configPath.includes('/')
            ? path.dirname(configPath).replace(/^src\//, '').replace(/[\/\\]/g, '_')
            : 'global';

          agents.push({
            id,
            path: configPath,
            config,
          });
        }
      }
    }

    res.status(200).json({ agents });
  } else {
    res.setHeader('Allow', ['GET']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}