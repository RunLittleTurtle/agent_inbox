import { auth } from '@clerk/nextjs/server';
import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const SUPABASE_SECRET_KEY = process.env.SUPABASE_SECRET_KEY!;

export async function POST(req: NextRequest) {
  try {
    // Get authenticated user from Clerk
    const { userId } = await auth();

    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized - Please sign in' },
        { status: 401 }
      );
    }

    // Fetch user-specific API key from Supabase
    const supabase = createClient(SUPABASE_URL, SUPABASE_SECRET_KEY);
    const { data: userSecrets, error: secretsError } = await supabase
      .from('user_secrets')
      .select('openai_api_key')
      .eq('clerk_id', userId)
      .maybeSingle();

    if (secretsError) {
      console.error('Error fetching user secrets:', secretsError);
      return NextResponse.json(
        { error: 'Failed to fetch API key configuration' },
        { status: 403 }
      );
    }

    const apiKey = userSecrets?.openai_api_key;

    if (!apiKey) {
      console.error('OpenAI API key not configured for user:', userId);
      return NextResponse.json(
        { error: 'OpenAI API key not configured. Please add your API key in the config page.' },
        { status: 403 }
      );
    }

    // Get audio file from request
    const formData = await req.formData();
    const audioFile = formData.get('file');

    if (!audioFile || !(audioFile instanceof File)) {
      return NextResponse.json(
        { error: 'No audio file provided' },
        { status: 400 }
      );
    }

    // Forward to OpenAI API
    const openaiFormData = new FormData();
    openaiFormData.append('file', audioFile);
    openaiFormData.append('model', 'whisper-1');
    openaiFormData.append('response_format', 'json');

    const response = await fetch(
      'https://api.openai.com/v1/audio/transcriptions',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${apiKey}`,
        },
        body: openaiFormData,
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('OpenAI API error:', errorData);
      return NextResponse.json(
        {
          error: errorData.error?.message || `OpenAI API error: ${response.status} ${response.statusText}`,
        },
        { status: response.status }
      );
    }

    const result = await response.json();

    return NextResponse.json({
      text: result.text?.trim() || '',
      language: result.language,
    });
  } catch (error) {
    console.error('Transcription API error:', error);
    return NextResponse.json(
      { error: 'Transcription failed' },
      { status: 500 }
    );
  }
}