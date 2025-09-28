import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';

function getCurrentEnvValues() {
  try {
    // Get the project root - go up from config-app directory to main project
    const projectRoot = path.join(process.cwd(), '..');
    const envPath = path.join(projectRoot, '.env');

    // IMPORTANT: Force reload from disk, don't use cached process.env
    // This ensures we get fresh values after updates
    const envConfig = config({ path: envPath, override: true });

    // Also read the file directly for env vars that might not be in process.env
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const envVars: Record<string, string> = {};

      envContent.split('\n').forEach(line => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const [key, ...valueParts] = trimmed.split('=');
          if (key) {
            envVars[key.trim()] = valueParts.join('=').trim();
          }
        }
      });

      // Merge with process.env, preferring fresh file values
      return { ...process.env, ...envVars };
    }

    return process.env;
  } catch (error) {
    console.error('Error reading .env file:', error);
    return {};
  }
}

function getPythonConfigValues(agentId: string | null) {
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

        // Read prompts from prompt.py
        const promptPath = path.join(projectRoot, 'src/_react_agent_mcp_template/prompt.py');
        let promptTemplates = {};
        if (fs.existsSync(promptPath)) {
          const promptContent = fs.readFileSync(promptPath, 'utf8');

          // Extract prompts using multiline regex
          const systemPromptMatch = promptContent.match(/AGENT_SYSTEM_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const rolePromptMatch = promptContent.match(/AGENT_ROLE_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const guidelinesPromptMatch = promptContent.match(/AGENT_GUIDELINES_PROMPT\s*=\s*"""([\s\S]*?)"""/);

          promptTemplates = {
            agent_system_prompt: systemPromptMatch?.[1] || '',
            agent_role_prompt: rolePromptMatch?.[1] || '',
            agent_guidelines_prompt: guidelinesPromptMatch?.[1] || ''
          };
        }

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
          },
          prompt_templates: promptTemplates
        };
      }
    }

    if (agentId === 'email_agent') {
      // Read values from the email agent's config.py
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, 'src/email_agent/config.py');

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
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.3,
            max_tokens: maxTokensMatch ? parseInt(maxTokensMatch[1]) : 2000,
            streaming: streamingMatch?.[1] === 'True'
          },
          agent_identity: {
            agent_name: agentNameMatch?.[1] || 'email',
            agent_display_name: displayNameMatch?.[1] || 'Email',
            agent_description: descriptionMatch?.[1] || 'email management and Gmail operations',
            mcp_service: mcpServiceMatch?.[1] || 'google_gmail'
          }
        };
      }
    }

    if (agentId === 'calendar_agent') {
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, 'src/calendar_agent/config.py');

      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');

        // LLM Config
        const modelMatch = content.match(/"model":\s*"([^"]+)"/);
        const tempMatch = content.match(/"temperature":\s*([\d.]+)/);

        // Agent Identity
        const agentNameMatch = content.match(/AGENT_NAME\s*=\s*"([^"]+)"/);
        const displayNameMatch = content.match(/AGENT_DISPLAY_NAME\s*=\s*"([^"]+)"/);
        const descriptionMatch = content.match(/AGENT_DESCRIPTION\s*=\s*"([^"]+)"/);
        const statusMatch = content.match(/AGENT_STATUS\s*=\s*"([^"]+)"/);

        // MCP Connection
        const envValues = getCurrentEnvValues();

        // User Preferences
        const timezoneMatch = content.match(/CALENDAR_TIMEZONE\s*=\s*'([^']+)'/);
        const workStartMatch = content.match(/WORK_HOURS_START\s*=\s*'([^']+)'/);
        const workEndMatch = content.match(/WORK_HOURS_END\s*=\s*'([^']+)'/);
        const meetingDurationMatch = content.match(/DEFAULT_MEETING_DURATION\s*=\s*'([^']+)'/);

        // Read prompts from prompt.py
        const promptPath = path.join(projectRoot, 'src/calendar_agent/prompt.py');
        let promptTemplates = {};
        if (fs.existsSync(promptPath)) {
          const promptContent = fs.readFileSync(promptPath, 'utf8');

          // Extract prompts using multiline regex - match the actual variable names from prompt.py
          const systemPromptMatch = promptContent.match(/AGENT_SYSTEM_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const rolePromptMatch = promptContent.match(/AGENT_ROLE_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const guidelinesPromptMatch = promptContent.match(/AGENT_GUIDELINES_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const routingPromptMatch = promptContent.match(/ROUTING_SYSTEM_PROMPT\s*=\s*"""([\s\S]*?)"""/);
          const bookingPromptMatch = promptContent.match(/BOOKING_EXTRACTION_PROMPT_TEMPLATE\s*=\s*"""([\s\S]*?)"""/);

          promptTemplates = {
            agent_system_prompt: systemPromptMatch?.[1] || '',
            agent_role_prompt: rolePromptMatch?.[1] || '',
            agent_guidelines_prompt: guidelinesPromptMatch?.[1] || '',
            routing_system_prompt: routingPromptMatch?.[1] || '',
            booking_extraction_prompt: bookingPromptMatch?.[1] || ''
          };
        }

        return {
          agent_identity: {
            agent_name: agentNameMatch?.[1] || 'calendar',
            agent_display_name: displayNameMatch?.[1] || 'Calendar Agent',
            agent_description: descriptionMatch?.[1] || 'Google Calendar management and scheduling',
            agent_status: statusMatch?.[1] || 'active'
          },
          llm: {
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.3
          },
          mcp_connection: {
            calendar_mcp_url: envValues.PIPEDREAM_MCP_SERVER || ''
          },
          user_preferences: {
            timezone: timezoneMatch?.[1] || 'global',
            work_hours_start: workStartMatch?.[1] || '09:00',
            work_hours_end: workEndMatch?.[1] || '17:00',
            default_meeting_duration: meetingDurationMatch?.[1] || '30'
          },
          prompt_templates: promptTemplates
        };
      }
    }

    if (agentId === 'drive_react_agent') {
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, 'src/drive_react_agent/config.py');

      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');

        const modelMatch = content.match(/"model":\s*"([^"]+)"/);
        const tempMatch = content.match(/"temperature":\s*([\d.]+)/);

        return {
          llm: {
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.2
          }
        };
      }
    }

    if (agentId === 'job_search_agent') {
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, 'src/job_search_agent/config.py');

      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf8');

        const modelMatch = content.match(/"model":\s*"([^"]+)"/);
        const tempMatch = content.match(/"temperature":\s*([\d.]+)/);

        return {
          llm: {
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0
          }
        };
      }
    }
  } catch (error) {
    console.error('Error reading Python config values:', error);
  }

  return {};
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const agentId = searchParams.get('agentId');

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

    return NextResponse.json({
      success: true,
      values: mergedValues,
      agentId,
    });
  } catch (error) {
    console.error('Error getting config values:', error);
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to retrieve configuration values',
      },
      { status: 500 }
    );
  }
}