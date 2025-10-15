/**
 * Supabase Singleton Client
 *
 * Creates a single shared Supabase client instance to avoid the warning:
 * "Multiple GoTrueClient instances detected in the same browser context"
 *
 * This pattern ensures only one client exists per storage key.
 */
import { createClient, SupabaseClient } from "@supabase/supabase-js";

let supabaseInstance: SupabaseClient | null = null;

/**
 * Get or create the singleton Supabase client
 */
export function getSupabaseClient(): SupabaseClient | null {
  // Return existing instance if it exists
  if (supabaseInstance) {
    return supabaseInstance;
  }

  // Create new instance if environment variables are available
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

  if (!supabaseUrl || !supabaseKey) {
    console.warn("Supabase credentials not configured");
    return null;
  }

  // Create and cache the singleton instance
  supabaseInstance = createClient(supabaseUrl, supabaseKey);

  return supabaseInstance;
}

/**
 * Clear the singleton instance (useful for testing or re-initialization)
 */
export function clearSupabaseClient(): void {
  supabaseInstance = null;
}
