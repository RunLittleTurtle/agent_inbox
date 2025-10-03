import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';
import yaml from 'js-yaml';
import modelConstants from '../../../../../config/model_constants.json';

const CONFIG_API_URL = process.env.NEXT_PUBLIC_CONFIG_API_URL || 'http://localhost:8000';

function getCurrentEnvValues(): Record<string, string> {
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

      // Return fresh file values only - no need to merge with process.env
      // since we only need user-defined values from .env (API keys, MCP URLs, etc.)
      return envVars;
    }

    return {};
  } catch (error) {
    console.error('Error reading .env file:', error);
    return {};
  }
}

function getPythonConfigValues(agentId: string | null) {
  try {
    if (agentId === '_react_agent_mcp_template' || agentId === 'multi_tool_rube_agent') {
      // Read values from the agent's config.py
      const projectRoot = path.join(process.cwd(), '..');
      const configPath = path.join(projectRoot, `src/${agentId}/config.py`);

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
        const statusMatch = content.match(/AGENT_STATUS\s*=\s*"([^"]+)"/);

        // Extract timezone
        const timezoneMatch = content.match(/TEMPLATE_TIMEZONE\s*=\s*'([^']+)'/);

        // Extract MCP Configuration - new simplified approach
        const mcpEnvVarMatch = content.match(/MCP_ENV_VAR\s*=\s*["']([^"']+)["']/);
        let mcpEnvVar = mcpEnvVarMatch?.[1] || '';
        let mcpServerUrl = '';

        // Only get the URL if we have a valid env var name (not a placeholder)
        if (mcpEnvVar && !mcpEnvVar.includes('{')) {
          const envValues = getCurrentEnvValues();
          mcpServerUrl = envValues[mcpEnvVar] || '';
        }

        // Read prompts from prompt.py
        const promptPath = path.join(projectRoot, `src/${agentId}/prompt.py`);
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
            model: modelMatch?.[1] || modelConstants.DEFAULT_LLM_MODEL,
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.2,
            max_tokens: maxTokensMatch ? parseInt(maxTokensMatch[1]) : 2000,
            streaming: streamingMatch?.[1] === 'True'
          },
          agent_identity: {
            agent_name: agentNameMatch?.[1] || '{AGENT_NAME}',
            agent_display_name: displayNameMatch?.[1] || '{AGENT_DISPLAY_NAME}',
            agent_description: descriptionMatch?.[1] || '{AGENT_DESCRIPTION}',
            agent_status: statusMatch?.[1] || 'active'
          },
          user_preferences: {
            timezone: timezoneMatch?.[1] || 'global'
          },
          mcp_integration: {
            mcp_env_var: mcpEnvVar,
            mcp_server_url: mcpServerUrl
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
            model: modelMatch?.[1] || modelConstants.DEFAULT_LLM_MODEL,
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

        // MCP Configuration - read the environment variable name
        const mcpEnvVarMatch = content.match(/MCP_ENV_VAR\s*=\s*["']([^"']+)["']/);
        let mcpEnvVar = mcpEnvVarMatch?.[1] || 'PIPEDREAM_MCP_SERVER';
        let mcpServerUrl = '';

        // Get the URL from the environment variable
        if (mcpEnvVar) {
          const envValues = getCurrentEnvValues();
          mcpServerUrl = envValues[mcpEnvVar] || '';
        }

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
            model: modelMatch?.[1] || modelConstants.DEFAULT_LLM_MODEL,
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.3
          },
          mcp_integration: {
            mcp_env_var: mcpEnvVar,
            mcp_server_url: mcpServerUrl
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
            model: modelMatch?.[1] || modelConstants.DEFAULT_LLM_MODEL,
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
            model: modelMatch?.[1] || modelConstants.DEFAULT_LLM_MODEL,
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0
          }
        };
      }
    }

    // REMOVED: Old file-based Executive AI Assistant handling
    // Now uses FastAPI bridge like all other agents (see line ~497)
  } catch (error) {
    console.error('Error reading Python config values:', error);
  }

  return {};
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const agentId = searchParams.get('agentId');

  try {
    // Get authenticated user
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized - Please sign in' },
        { status: 401 }
      );
    }

    // Handle global environment configuration
    if (!agentId || agentId === 'global') {
      // ✅ Read from Supabase via FastAPI (with .env fallback)
      const CONFIG_API_URL = process.env.NEXT_PUBLIC_CONFIG_API_URL || 'http://localhost:8000';
      const fastapiUrl = `${CONFIG_API_URL}/api/config/values?agent_id=global&user_id=${userId}`;

      try {
        const fastapiResponse = await fetch(fastapiUrl);

        if (fastapiResponse.ok) {
          const fastapiData = await fastapiResponse.json();

          // FastAPI returns values directly, wrap them properly
          return NextResponse.json({
            success: true,
            values: fastapiData,
            agentId: 'global',
            source: 'supabase'
          });
        } else {
          console.warn(`FastAPI returned ${fastapiResponse.status}, falling back to .env`);
          throw new Error('FastAPI not available');
        }
      } catch (error) {
        // Fallback to .env if Supabase/FastAPI unavailable
        console.warn('Falling back to .env for global config:', error);
        const envValues = getCurrentEnvValues();

        const globalConfigValues = {
          user_preferences: {
            user_timezone: envValues.USER_TIMEZONE || modelConstants.DEFAULT_TIMEZONE
          },
          ai_models: {
            anthropic_api_key: envValues.ANTHROPIC_API_KEY || '',
            openai_api_key: envValues.OPENAI_API_KEY || ''
          },
          langgraph_system: {
            langsmith_api_key: envValues.LANGSMITH_API_KEY || '',
            langchain_project: envValues.LANGCHAIN_PROJECT || 'ambient-email-agent'
          }
        };

        return NextResponse.json({
          success: true,
          values: globalConfigValues,
          agentId: 'global',
          source: 'env-fallback'
        });
      }
    }

    // Handle Interface UIs configuration
    if (agentId === 'interface_uis') {
      const envValues = getCurrentEnvValues();

      // Return values organized by sections as defined in interface_uis_config.py
      const interfaceUIsValues = {
        agent_chat_ui_1: {
          chat1_deployment_url: envValues.LANGGRAPH_DEPLOYMENT_URL || 'http://localhost:2024',
          chat1_graph_id: envValues.AGENT_INBOX_GRAPH_ID || 'agent',
          chat1_langsmith_key: envValues.LANGSMITH_API_KEY || ''
        },
        agent_chat_ui_2: {
          chat2_deployment_url: envValues.LANGGRAPH_DEPLOYMENT_URL || 'http://localhost:2024',
          chat2_graph_id: envValues.AGENT_INBOX_GRAPH_ID || 'agent',
          chat2_langsmith_key: envValues.LANGSMITH_API_KEY || ''
        },
        agent_inbox_multi: {
          multi_graph_id: envValues.AGENT_INBOX_GRAPH_ID || 'agent',
          multi_deployment_url: envValues.LANGGRAPH_DEPLOYMENT_URL || 'http://localhost:2024',
          multi_name: 'Multi-Agent System'
        },
        agent_inbox_executive: {
          exec_graph_id: 'main',
          exec_deployment_url: 'http://localhost:2025',
          exec_name: 'Executive AI Assistant'
        }
      };

      return NextResponse.json({
        success: true,
        values: interfaceUIsValues,
        agentId: 'interface_uis',
      });
    }

    // ✅ PHASE 4: Call FastAPI Bridge for agent-specific configs
    // FastAPI reads Python defaults + merges with Supabase user overrides
    console.log(`[Phase 4] Calling FastAPI bridge for agent: ${agentId}, user: ${userId}`);

    const fastapiUrl = `${CONFIG_API_URL}/api/config/values?agent_id=${agentId}&user_id=${userId}`;
    const fastapiResponse = await fetch(fastapiUrl);

    if (!fastapiResponse.ok) {
      console.error(`FastAPI error: ${fastapiResponse.status} ${fastapiResponse.statusText}`);
      throw new Error(`FastAPI returned status ${fastapiResponse.status}`);
    }

    const fastapiData = await fastapiResponse.json();
    console.log(`[Phase 4] Received merged config from FastAPI for ${agentId}`);

    return NextResponse.json({
      success: true,
      values: fastapiData.values,
      agentId,
      source: 'fastapi-bridge' // Mark that this came from the new bridge
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