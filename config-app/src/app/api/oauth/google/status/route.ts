/**
 * Check Google OAuth Connection Status
 * Returns whether the user has a valid refresh_token
 */

import { NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { createClient } from '@supabase/supabase-js';

export async function GET() {
  try {
    // 1. Get authenticated user from Clerk
    const { userId } = await auth();
    if (!userId) {
      return NextResponse.json({ connected: false }, { status: 401 });
    }

    // 2. Check Supabase for refresh_token
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SECRET_KEY;

    if (!supabaseUrl || !supabaseKey) {
      console.error('[Google OAuth Status] Supabase configuration missing');
      return NextResponse.json({ connected: false, error: 'Configuration error' }, { status: 500 });
    }

    const supabase = createClient(supabaseUrl, supabaseKey);

    const { data: userSecrets, error: fetchError } = await supabase
      .from('user_secrets')
      .select('google_refresh_token')
      .eq('clerk_id', userId)
      .maybeSingle();

    if (fetchError) {
      console.error('[Google OAuth Status] Supabase error:', fetchError);
      return NextResponse.json({ connected: false, error: 'Database error' }, { status: 500 });
    }

    // 3. Check if refresh_token exists and is not empty
    const hasToken = userSecrets?.google_refresh_token && userSecrets.google_refresh_token.length > 0;

    return NextResponse.json({
      connected: hasToken,
      timestamp: Date.now()
    });

  } catch (error: any) {
    console.error('[Google OAuth Status] Error:', error);
    return NextResponse.json(
      { connected: false, error: error.message || 'Unknown error' },
      { status: 500 }
    );
  }
}
