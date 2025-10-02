/**
 * POST /api/config/reset
 *
 * Resets configuration values to defaults through FastAPI bridge.
 * Supports three modes:
 * 1. Reset all configs (no section/field specified)
 * 2. Reset entire section (section_key specified)
 * 3. Reset single field (both section_key and field_key specified)
 */

import { auth } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';

const CONFIG_API_URL = process.env.NEXT_PUBLIC_CONFIG_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get authenticated user
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized - Please sign in' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await request.json();
    const { agent_id, section_key, field_key } = body;

    if (!agent_id) {
      return NextResponse.json(
        { error: 'Missing required field: agent_id' },
        { status: 400 }
      );
    }

    console.log(`[Phase 4] Resetting config for agent: ${agent_id}, user: ${userId}`);
    if (section_key) console.log(`  Section: ${section_key}`);
    if (field_key) console.log(`  Field: ${field_key}`);

    // Call FastAPI bridge reset endpoint
    const fastapiUrl = `${CONFIG_API_URL}/api/config/reset`;
    const fastapiResponse = await fetch(fastapiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        agent_id,
        user_id: userId,
        section_key: section_key || null,
        field_key: field_key || null,
      }),
    });

    if (!fastapiResponse.ok) {
      console.error(`FastAPI error: ${fastapiResponse.status} ${fastapiResponse.statusText}`);
      const errorData = await fastapiResponse.json();
      throw new Error(errorData.detail || `FastAPI returned status ${fastapiResponse.status}`);
    }

    const fastapiData = await fastapiResponse.json();
    console.log(`[Phase 4] Reset successful: ${fastapiData.action}`);

    return NextResponse.json({
      success: true,
      action: fastapiData.action,
      message: fastapiData.message,
      source: 'fastapi-bridge',
    });
  } catch (error) {
    console.error('Error resetting config:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to reset configuration',
      },
      { status: 500 }
    );
  }
}
