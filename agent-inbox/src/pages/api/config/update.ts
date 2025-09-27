import type { NextApiRequest, NextApiResponse } from 'next';
import fs from 'fs';
import path from 'path';

interface UpdateConfigRequest {
  agentId: string;
  configPath: string;
  sectionKey: string;
  fieldKey: string;
  value: any;
  envVar?: string;
}

function updateEnvVariable(envVar: string, value: any) {
  try {
    // Get the project root - go up from agent-inbox directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const envPath = path.join(projectRoot, '.env');

    let envContent = '';
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }

    const lines = envContent.split('\n');
    const envVarRegex = new RegExp(`^${envVar}=`);
    let updated = false;

    // Find and update existing variable
    for (let i = 0; i < lines.length; i++) {
      if (envVarRegex.test(lines[i])) {
        lines[i] = `${envVar}=${value}`;
        updated = true;
        break;
      }
    }

    // Add new variable if not found
    if (!updated) {
      lines.push(`${envVar}=${value}`);
    }

    // Write back to .env file
    fs.writeFileSync(envPath, lines.join('\n'));
    return true;
  } catch (error) {
    console.error('Error updating .env file:', error);
    return false;
  }
}

function updateConfigFile(configPath: string, sectionKey: string, fieldKey: string, value: any) {
  try {
    // Get the project root - go up from agent-inbox directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const fullPath = path.join(projectRoot, configPath);

    if (!fs.existsSync(fullPath)) {
      console.error(`Config file not found: ${fullPath}`);
      return false;
    }

    // Special handling for the React Agent MCP template
    if (configPath.includes('_react_agent_mcp_template')) {
      // For the template, update the config.py file instead of ui_config.py
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Template config.py not found: ${configPyPath}`);
        return false;
      }

      let configContent = fs.readFileSync(configPyPath, 'utf8');

      // Update LLM_CONFIG fields
      if (sectionKey === 'llm') {
        if (fieldKey === 'model') {
          // Update the model in LLM_CONFIG
          configContent = configContent.replace(
            /("model":\s*")([^"]+)(")/,
            `$1${value}$3`
          );
        } else if (fieldKey === 'temperature') {
          // Update temperature - handle both string and number
          configContent = configContent.replace(
            /("temperature":\s*)([\d.]+)/,
            `$1${value}`
          );
        } else if (fieldKey === 'max_tokens') {
          // Update max_tokens if it exists, or add it
          if (configContent.includes('"max_tokens"')) {
            configContent = configContent.replace(
              /("max_tokens":\s*)([\d]+)/,
              `$1${value}`
            );
          } else {
            // Add max_tokens to LLM_CONFIG
            configContent = configContent.replace(
              /("streaming":\s*False)(,?)(\s*\n\s*})/,
              `$1,\n    "max_tokens": ${value}$3`
            );
          }
        } else if (fieldKey === 'streaming') {
          configContent = configContent.replace(
            /("streaming":\s*)(True|False)/,
            `$1${value ? 'True' : 'False'}`
          );
        }
      }
      // Update agent identity fields
      else if (sectionKey === 'agent_identity') {
        const mappings: Record<string, string> = {
          'agent_name': 'AGENT_NAME',
          'agent_display_name': 'AGENT_DISPLAY_NAME',
          'agent_description': 'AGENT_DESCRIPTION',
          'mcp_service': 'MCP_SERVICE'
        };

        const varName = mappings[fieldKey];
        if (varName) {
          const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
          configContent = configContent.replace(regex, `$1${value}$3`);
        }
      }

      // Write the updated content back
      fs.writeFileSync(configPyPath, configContent, 'utf8');
      console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
      return true;
    }

    // Special handling for email_agent
    if (configPath.includes('email_agent')) {
      // For the email agent, update the config.py file instead of ui_config.py
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Email agent config.py not found: ${configPyPath}`);
        return false;
      }

      let configContent = fs.readFileSync(configPyPath, 'utf8');

      // Update LLM_CONFIG fields
      if (sectionKey === 'llm') {
        if (fieldKey === 'model') {
          configContent = configContent.replace(
            /("model":\s*")([^"]+)(")/,
            `$1${value}$3`
          );
        } else if (fieldKey === 'temperature') {
          configContent = configContent.replace(
            /("temperature":\s*)([\d.]+)/,
            `$1${value}`
          );
        } else if (fieldKey === 'max_tokens') {
          if (configContent.includes('"max_tokens"')) {
            configContent = configContent.replace(
              /("max_tokens":\s*)([\d]+)/,
              `$1${value}`
            );
          } else {
            configContent = configContent.replace(
              /("streaming":\s*False)(,?)(\s*\n\s*})/,
              `$1,\n    "max_tokens": ${value}$3`
            );
          }
        } else if (fieldKey === 'streaming') {
          configContent = configContent.replace(
            /("streaming":\s*)(True|False)/,
            `$1${value ? 'True' : 'False'}`
          );
        }
      }
      // Update agent identity fields
      else if (sectionKey === 'agent_identity') {
        const mappings: Record<string, string> = {
          'agent_name': 'AGENT_NAME',
          'agent_display_name': 'AGENT_DISPLAY_NAME',
          'agent_description': 'AGENT_DESCRIPTION',
          'mcp_service': 'MCP_SERVICE'
        };

        const varName = mappings[fieldKey];
        if (varName) {
          const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
          configContent = configContent.replace(regex, `$1${value}$3`);
        }
      }

      // Write the updated content back
      fs.writeFileSync(configPyPath, configContent, 'utf8');
      console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
      return true;
    }

    // For other Python config files, implement similar logic as needed
    console.warn(`Config file updates not implemented for: ${configPath}`);
    return false;

  } catch (error) {
    console.error('Error updating config file:', error);
    return false;
  }
}

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    const { agentId, configPath, sectionKey, fieldKey, value, envVar } = req.body as UpdateConfigRequest;

    try {
      let success = true;

      // If this field has an environment variable, update .env
      if (envVar) {
        success = updateEnvVariable(envVar, value);
      } else {
        // Otherwise, update the config file directly
        success = updateConfigFile(configPath, sectionKey, fieldKey, value);
      }

      if (success) {
        res.status(200).json({
          success: true,
          message: `Updated ${fieldKey} for ${agentId}`,
        });
      } else {
        res.status(500).json({
          success: false,
          error: 'Failed to update configuration',
        });
      }
    } catch (error) {
      console.error('Update error:', error);
      res.status(500).json({
        success: false,
        error: 'Internal server error',
      });
    }
  } else {
    res.setHeader('Allow', ['POST']);
    res.status(405).end(`Method ${req.method} Not Allowed`);
  }
}