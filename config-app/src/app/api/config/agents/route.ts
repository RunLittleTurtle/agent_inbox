import { NextRequest, NextResponse } from 'next/server';
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
  'interface_uis_config.py',
  'src/_react_agent_mcp_template/ui_config.py',
  'src/multi_tool_rube_agent/ui_config.py',
  'src/calendar_agent/ui_config.py',
  'src/drive_react_agent/ui_config.py',
  'src/executive-ai-assistant/ui_config.py',
  'src/job_search_agent/ui_config.py',
  'src/email_agent/ui_config.py',
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

    // Define the standard LLM model options - CENTRALIZED LIST
    // Changing this list will update ALL agents using STANDARD_LLM_MODEL_OPTIONS
    const STANDARD_LLM_MODEL_OPTIONS = [
      'claude-sonnet-4-20250514',
      'claude-3-5-haiku-20241022',
      'gpt-5',
      'gpt-4o',
      'o3',
      'claude-opus-4-1-20250805'
    ];

    // Convert Python dict syntax to JSON (basic conversion)
    const configInfoStr = configInfoMatch[1]
      .replace(/'/g, '"')
      .replace(/True/g, 'true')
      .replace(/False/g, 'false')
      .replace(/None/g, 'null');

    let configSectionsStr = configSectionsMatch[1]
      .replace(/'/g, '"')
      .replace(/True/g, 'true')
      .replace(/False/g, 'false')
      .replace(/None/g, 'null');

    // Replace STANDARD_LLM_MODEL_OPTIONS with the actual array
    configSectionsStr = configSectionsStr.replace(
      /STANDARD_LLM_MODEL_OPTIONS/g,
      JSON.stringify(STANDARD_LLM_MODEL_OPTIONS)
    );

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

export async function GET(request: NextRequest) {
  const agents: Array<{
    id: string;
    path: string;
    config: AgentConfigData;
  }> = [];

  // Get the project root - go up from config-app directory to main project
  const projectRoot = path.join(process.cwd(), '..');

  console.log('Current working directory:', process.cwd());
  console.log('Project root resolved to:', projectRoot);

  for (const configPath of AGENT_CONFIG_PATHS) {
    const fullPath = path.join(projectRoot, configPath);

    console.log(`Checking path: ${fullPath}, exists: ${fs.existsSync(fullPath)}`);

    if (fs.existsSync(fullPath)) {
      const config = parseConfigFile(fullPath);
      if (config) {
        // Generate ID from file path
        const id = configPath.includes('/')
          ? path.dirname(configPath).replace(/^src\//, '').replace(/[\/\\]/g, '_')
          : configPath === 'interface_uis_config.py'
            ? 'interface_uis'
            : 'global';

        agents.push({
          id,
          path: configPath,
          config,
        });
      }
    }
  }

  return NextResponse.json({ agents });
}