import { NextRequest, NextResponse } from 'next/server';

const CONFIG_API_URL = process.env.NEXT_PUBLIC_CONFIG_API_URL || 'http://localhost:8000';

/**
 * GET /api/config/agents
 *
 * Proxies to FastAPI backend to get agent configuration schemas
 * The backend reads Python ui_config.py files and returns structured data
 */
export async function GET(request: NextRequest) {
  try {
    console.log('[/api/config/agents] Fetching from:', `${CONFIG_API_URL}/api/config/schemas`);

    const response = await fetch(`${CONFIG_API_URL}/api/config/schemas`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('[/api/config/agents] Backend error:', response.status, response.statusText);
      throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    console.log('[/api/config/agents] Received', data.agents?.length || 0, 'agents');

    return NextResponse.json(data);
  } catch (error) {
    console.error('[/api/config/agents] Error:', error);

    return NextResponse.json(
      {
        error: 'Failed to fetch agent configurations',
        details: error instanceof Error ? error.message : 'Unknown error',
        agents: [] // Return empty array to prevent frontend crash
      },
      { status: 500 }
    );
  }
}
