import { NextRequest, NextResponse } from 'next/server';
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
    // Get the project root - go up from config-app directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const envPath = path.join(projectRoot, '.env');

    let envContent = '';
    if (fs.existsSync(envPath)) {
      envContent = fs.readFileSync(envPath, 'utf8');
    }

    const lines = envContent.split('\n');
    const envVarRegex = new RegExp(`^${envVar}=`);
    let updated = false;

    // Special handling for 'global' value - store as empty string in .env
    const envValue = value === 'global' ? '' : value;

    // Find and update existing variable
    for (let i = 0; i < lines.length; i++) {
      if (envVarRegex.test(lines[i])) {
        lines[i] = `${envVar}=${envValue}`;
        updated = true;
        break;
      }
    }

    // Add new variable if not found
    if (!updated) {
      lines.push(`${envVar}=${envValue}`);
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
    // Get the project root - go up from config-app directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const fullPath = path.join(projectRoot, configPath);

    if (!fs.existsSync(fullPath)) {
      console.error(`Config file not found: ${fullPath}`);
      return false;
    }

    // Special handling for the React Agent MCP template
    if (configPath.includes('_react_agent_mcp_template')) {
      // For the template, update prompt.py for prompts, config.py for other settings
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');
      const promptPyPath = fullPath.replace('ui_config.py', 'prompt.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Template config.py not found: ${configPyPath}`);
        return false;
      }

      let configContent = fs.readFileSync(configPyPath, 'utf8');

      // Handle MCP integration fields specially for dynamic env vars
      if (sectionKey === 'mcp_integration' && fieldKey === 'mcp_server_url') {
        // For MCP server URL, we need to get the current MCP_SERVICE value
        // and update the correct environment variable
        const mcpServiceMatch = configContent.match(/MCP_SERVICE\s*=\s*"([^"]+)"/);
        if (mcpServiceMatch) {
          const mcpService = mcpServiceMatch[1];
          // Skip if it's still a placeholder
          if (!mcpService.includes('{')) {
            const dynamicEnvVar = `PIPEDREAM_MCP_SERVER_${mcpService}`;
            // Update the environment variable in .env
            return updateEnvVariable(dynamicEnvVar, value);
          }
        }
      }

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
          'mcp_service': 'MCP_SERVICE',
          'agent_status': 'AGENT_STATUS'
        };

        const varName = mappings[fieldKey];
        if (varName) {
          const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
          configContent = configContent.replace(regex, `$1${value}$3`);
        }
      }
      // Update agent configuration fields
      else if (sectionKey === 'agent_configuration') {
        if (fieldKey === 'agent_prompt') {
          // Update the AGENT_PROMPT multi-line string
          const promptRegex = /AGENT_PROMPT\s*=\s*"""[\s\S]*?"""/;
          configContent = configContent.replace(promptRegex, `AGENT_PROMPT = """${value}"""`);
        }
      }
      // Update prompt templates fields - these go to prompt.py per LangGraph best practices
      else if (sectionKey === 'prompt_templates') {
        // Read prompt.py file instead
        if (!fs.existsSync(promptPyPath)) {
          console.error(`Template prompt.py not found: ${promptPyPath}`);
          return false;
        }

        let promptContent = fs.readFileSync(promptPyPath, 'utf8');

        if (fieldKey === 'agent_system_prompt') {
          // Update the AGENT_SYSTEM_PROMPT multi-line string
          const promptRegex = /AGENT_SYSTEM_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_SYSTEM_PROMPT = """${value}"""`);
        } else if (fieldKey === 'agent_role_prompt') {
          // Update the AGENT_ROLE_PROMPT multi-line string
          const promptRegex = /AGENT_ROLE_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_ROLE_PROMPT = """${value}"""`);
        } else if (fieldKey === 'agent_guidelines_prompt') {
          // Update the AGENT_GUIDELINES_PROMPT multi-line string
          const promptRegex = /AGENT_GUIDELINES_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_GUIDELINES_PROMPT = """${value}"""`);
        }

        // Write the updated content back to prompt.py
        fs.writeFileSync(promptPyPath, promptContent, 'utf8');
        console.log(`Successfully updated ${fieldKey} in ${promptPyPath}`);
        return true;
      }
      // Update user preferences fields
      else if (sectionKey === 'user_preferences') {
        if (fieldKey === 'timezone') {
          // Update TEMPLATE_TIMEZONE variable
          configContent = configContent.replace(
            /(TEMPLATE_TIMEZONE\s*=\s*')([^']+)(')/,
            `$1${value}$3`
          );
        }
      }

      // Write the updated content back to config.py (for non-prompt fields)
      if (sectionKey !== 'prompt_templates') {
        fs.writeFileSync(configPyPath, configContent, 'utf8');
        console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
      }
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
          'mcp_service': 'MCP_SERVICE',
          'agent_status': 'AGENT_STATUS'
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

    // Handler for calendar_agent
    if (configPath.includes('calendar_agent')) {
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');
      const promptPyPath = fullPath.replace('ui_config.py', 'prompt.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Calendar agent config.py not found: ${configPyPath}`);
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
        }
      }
      // Update agent identity fields
      else if (sectionKey === 'agent_identity') {
        const mappings: Record<string, string> = {
          'agent_name': 'AGENT_NAME',
          'agent_display_name': 'AGENT_DISPLAY_NAME',
          'agent_description': 'AGENT_DESCRIPTION',
          'agent_status': 'AGENT_STATUS'
        };

        const varName = mappings[fieldKey];
        if (varName) {
          const regex = new RegExp(`(${varName}\\s*=\\s*")([^"]+)(")`, 'g');
          configContent = configContent.replace(regex, `$1${value}$3`);
        }
      }
      // Update MCP connection fields - update .env instead
      else if (sectionKey === 'mcp_connection') {
        if (fieldKey === 'calendar_mcp_url') {
          // Update PIPEDREAM_MCP_SERVER environment variable
          return updateEnvVariable('PIPEDREAM_MCP_SERVER', value);
        }
      }
      // Update prompt templates fields - these go to prompt.py
      else if (sectionKey === 'prompt_templates') {
        if (!fs.existsSync(promptPyPath)) {
          console.error(`Calendar agent prompt.py not found: ${promptPyPath}`);
          return false;
        }

        let promptContent = fs.readFileSync(promptPyPath, 'utf8');

        if (fieldKey === 'agent_system_prompt') {
          // Update the AGENT_SYSTEM_PROMPT multi-line string
          const promptRegex = /AGENT_SYSTEM_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_SYSTEM_PROMPT = """${value}"""`);
        } else if (fieldKey === 'agent_role_prompt') {
          // Update the AGENT_ROLE_PROMPT multi-line string
          const promptRegex = /AGENT_ROLE_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_ROLE_PROMPT = """${value}"""`);
        } else if (fieldKey === 'agent_guidelines_prompt') {
          // Update the AGENT_GUIDELINES_PROMPT multi-line string
          const promptRegex = /AGENT_GUIDELINES_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `AGENT_GUIDELINES_PROMPT = """${value}"""`);
        } else if (fieldKey === 'routing_system_prompt') {
          // Update the ROUTING_SYSTEM_PROMPT multi-line string
          const promptRegex = /ROUTING_SYSTEM_PROMPT\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `ROUTING_SYSTEM_PROMPT = """${value}"""`);
        } else if (fieldKey === 'booking_extraction_prompt') {
          // Update the BOOKING_EXTRACTION_PROMPT_TEMPLATE multi-line string
          const promptRegex = /BOOKING_EXTRACTION_PROMPT_TEMPLATE\s*=\s*"""[\s\S]*?"""/;
          promptContent = promptContent.replace(promptRegex, `BOOKING_EXTRACTION_PROMPT_TEMPLATE = """${value}"""`);
        }

        // Write the updated content back to prompt.py
        fs.writeFileSync(promptPyPath, promptContent, 'utf8');
        console.log(`Successfully updated ${fieldKey} in ${promptPyPath}`);
        return true;
      }
      // Update user preferences fields
      else if (sectionKey === 'user_preferences') {
        if (fieldKey === 'timezone') {
          // Update CALENDAR_TIMEZONE variable
          configContent = configContent.replace(
            /(CALENDAR_TIMEZONE\s*=\s*')([^']+)(')/,
            `$1${value}$3`
          );
        } else if (fieldKey === 'work_hours_start') {
          configContent = configContent.replace(
            /(WORK_HOURS_START\s*=\s*')([^']+)(')/,
            `$1${value}$3`
          );
        } else if (fieldKey === 'work_hours_end') {
          configContent = configContent.replace(
            /(WORK_HOURS_END\s*=\s*')([^']+)(')/,
            `$1${value}$3`
          );
        } else if (fieldKey === 'default_meeting_duration') {
          configContent = configContent.replace(
            /(DEFAULT_MEETING_DURATION\s*=\s*')([^']+)(')/,
            `$1${value}$3`
          );
        }
      }

      // Write the updated content back to config.py (for non-prompt fields)
      if (sectionKey !== 'prompt_templates' && sectionKey !== 'mcp_connection') {
        fs.writeFileSync(configPyPath, configContent, 'utf8');
        console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
      }
      return true;
    }

    // Handler for drive_react_agent
    if (configPath.includes('drive_react_agent')) {
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Drive agent config.py not found: ${configPyPath}`);
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
        }
      }

      fs.writeFileSync(configPyPath, configContent, 'utf8');
      console.log(`Successfully updated ${fieldKey} in ${configPyPath}`);
      return true;
    }

    // Handler for job_search_agent
    if (configPath.includes('job_search_agent')) {
      const configPyPath = fullPath.replace('ui_config.py', 'config.py');

      if (!fs.existsSync(configPyPath)) {
        console.error(`Job search agent config.py not found: ${configPyPath}`);
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
        }
      }

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

export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as UpdateConfigRequest;
    const { agentId, configPath, sectionKey, fieldKey, value, envVar } = body;

    console.log('Update request:', { agentId, sectionKey, fieldKey, value, envVar });

    let success = true;

    // If this field has an environment variable, update .env
    if (envVar) {
      console.log(`Updating env var: ${envVar} = ${value}`);
      success = updateEnvVariable(envVar, value);
    } else {
      // Otherwise, update the config file directly
      console.log(`Updating config file: ${configPath}, ${sectionKey}.${fieldKey} = ${value}`);
      success = updateConfigFile(configPath, sectionKey, fieldKey, value);
    }

    if (success) {
      return NextResponse.json({
        success: true,
        message: `Updated ${fieldKey} for ${agentId}`,
      });
    } else {
      return NextResponse.json(
        {
          success: false,
          error: 'Failed to update configuration',
        },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('Update error:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Internal server error',
      },
      { status: 500 }
    );
  }
}