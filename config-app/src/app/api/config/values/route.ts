import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';
import { config } from 'dotenv';
import yaml from 'js-yaml';

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

        // Extract MCP Configuration - new simplified approach
        const mcpEnvVarMatch = content.match(/MCP_ENV_VAR\s*=\s*["']([^"']+)["']/);
        let mcpEnvVar = mcpEnvVarMatch?.[1] || '';
        let mcpServerUrl = '';

        // Only get the URL if we have a valid env var name (not a placeholder)
        if (mcpEnvVar && !mcpEnvVar.includes('{')) {
          const envValues = getCurrentEnvValues();
          mcpServerUrl = envValues[mcpEnvVar as string] || '';
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
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
            temperature: tempMatch ? parseFloat(tempMatch[1]) : 0.2,
            max_tokens: maxTokensMatch ? parseInt(maxTokensMatch[1]) : 2000,
            streaming: streamingMatch?.[1] === 'True'
          },
          agent_identity: {
            agent_name: agentNameMatch?.[1] || '{AGENT_NAME}',
            agent_display_name: displayNameMatch?.[1] || '{AGENT_DISPLAY_NAME}',
            agent_description: descriptionMatch?.[1] || '{AGENT_DESCRIPTION}'
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
            model: modelMatch?.[1] || 'claude-sonnet-4-20250514',
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

    if (agentId === 'executive-ai-assistant') {
      const projectRoot = path.join(process.cwd(), '..');
      const configYamlPath = path.join(projectRoot, 'src/executive-ai-assistant/eaia/main/config.yaml');

      if (fs.existsSync(configYamlPath)) {
        try {
          const yamlContent = fs.readFileSync(configYamlPath, 'utf8');
          const configData = yaml.load(yamlContent) as any;

          // Read credentials from executive assistant's .env file
          const envPath = path.join(projectRoot, 'src/executive-ai-assistant/.env');
          let aiModelKeys = {};
          let langsmithConfig = {};
          let googleCredentials = {};
          if (fs.existsSync(envPath)) {
            const envContent = fs.readFileSync(envPath, 'utf8');

            // AI Model API Keys - fix regex to not capture newlines
            const anthropicApiKeyMatch = envContent.match(/ANTHROPIC_API_KEY=([^\r\n]+)/);
            const openaiApiKeyMatch = envContent.match(/OPENAI_API_KEY=([^\r\n]+)/);

            aiModelKeys = {
              anthropic_api_key: anthropicApiKeyMatch?.[1]?.trim() || '',
              openai_api_key: openaiApiKeyMatch?.[1]?.trim() || ''
            };

            // LangSmith Configuration
            const langsmithApiKeyMatch = envContent.match(/LANGSMITH_API_KEY=([^\r\n]+)/);
            const langchainProjectMatch = envContent.match(/LANGCHAIN_PROJECT=([^\r\n]+)/);

            langsmithConfig = {
              langsmith_api_key: langsmithApiKeyMatch?.[1]?.trim() || '',
              langchain_project: langchainProjectMatch?.[1]?.trim() || 'ambient-email-agent'
            };

            // Google Workspace Credentials
            const googleClientIdMatch = envContent.match(/GOOGLE_CLIENT_ID=([^\r\n]+)/);
            const googleClientSecretMatch = envContent.match(/GOOGLE_CLIENT_SECRET=([^\r\n]+)/);
            const gmailRefreshTokenMatch = envContent.match(/GMAIL_REFRESH_TOKEN=([^\r\n]+)/);
            const emailAssociatedMatch = envContent.match(/EMAIL_ASSOCIATED=([^\r\n]+)/);

            googleCredentials = {
              google_client_id: googleClientIdMatch?.[1]?.trim() || '',
              google_client_secret: googleClientSecretMatch?.[1]?.trim() || '',
              gmail_refresh_token: gmailRefreshTokenMatch?.[1]?.trim() || '',
              user_google_email: emailAssociatedMatch?.[1]?.trim() || ''
            };
          }

          return {
            user_identity: {
              name: configData.name || '',
              full_name: configData.full_name || '',
              email: configData.email || '',
              background: configData.background || ''
            },
            user_preferences: {
              timezone: configData.timezone || 'America/Toronto',
              schedule_preferences: configData.schedule_preferences || ''
            },
            llm_triage: {
              triage_model: configData.triage_model || 'claude-3-5-haiku-20241022',
              triage_temperature: configData.triage_temperature || 0.1
            },
            llm_draft: {
              draft_model: configData.draft_model || 'claude-sonnet-4-20250514',
              draft_temperature: configData.draft_temperature || 0.2
            },
            llm_rewrite: {
              rewrite_model: configData.rewrite_model || 'claude-sonnet-4-20250514',
              rewrite_temperature: configData.rewrite_temperature || 0.3
            },
            llm_scheduling: {
              scheduling_model: configData.scheduling_model || 'gpt-4o',
              scheduling_temperature: configData.scheduling_temperature || 0.1
            },
            llm_reflection: {
              reflection_model: configData.reflection_model || 'claude-sonnet-4-20250514',
              reflection_temperature: configData.reflection_temperature || 0.1
            },
            email_preferences: {
              rewrite_preferences: configData.rewrite_preferences || ''
            },
            triage_prompts: {
              triage_no: configData.triage_no || '',
              triage_notify: configData.triage_notify || '',
              triage_email: configData.triage_email || ''
            },
            ai_models: aiModelKeys,
            langgraph_system: langsmithConfig,
            google_workspace: googleCredentials,
            agent_identity: {
              agent_name: 'executive-ai-assistant',
              agent_display_name: 'Executive AI Assistant',
              agent_description: 'AI-powered executive assistant for email management, scheduling, and task automation',
              agent_status: 'active'
            }
          };
        } catch (yamlError) {
          console.error('Error parsing config.yaml:', yamlError);
        }
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
    // Handle global environment configuration
    if (!agentId || agentId === 'global') {
      // Read all environment values for global config
      const envValues = getCurrentEnvValues();

      // Organize values by section as defined in ui_config.py
      const globalConfigValues = {
        user_preferences: {
          user_timezone: envValues.USER_TIMEZONE || 'America/Toronto'
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
      });
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

    // Get Python config values for agent-specific configs
    const pythonValues = getPythonConfigValues(agentId);

    // Only include essential global environment variables for agent configs
    // Do NOT include MCP server URLs as they are agent-specific
    const globalEnvValues = {
      ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY ? 'configured' : '',
      OPENAI_API_KEY: process.env.OPENAI_API_KEY ? 'configured' : '',
      USER_TIMEZONE: process.env.USER_TIMEZONE || 'America/Toronto'
    };

    // Merge only safe global values with agent-specific config
    const mergedValues = {
      ...globalEnvValues,
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