/**
 * Redis Client for OAuth State Storage
 * Stores PKCE code_verifier and session data during OAuth flow
 * Falls back to in-memory storage if Redis is unavailable
 */

import { createClient } from 'redis';

type RedisClientType = ReturnType<typeof createClient>;

let redisClient: RedisClientType | null = null;
let useInMemoryFallback = false;

// In-memory fallback for development (when Redis is unavailable)
const inMemoryStore: Map<string, { data: string; expiresAt: number }> = new Map();

/**
 * Get or create Redis client singleton
 */
export async function getRedisClient(): Promise<RedisClientType | null> {
  if (useInMemoryFallback) {
    return null;
  }

  if (redisClient) {
    return redisClient;
  }

  const redisUrl = process.env.REDIS_URI || process.env.KV_URL || process.env.UPSTASH_REDIS_REST_URL;

  if (!redisUrl) {
    console.warn('[Redis] No Redis URL configured, using in-memory fallback');
    useInMemoryFallback = true;
    return null;
  }

  try {
    redisClient = createClient({
      url: redisUrl
    });

    redisClient.on('error', (err) => {
      console.error('[Redis] Client Error:', err);
      // Don't crash, fall back to in-memory
      useInMemoryFallback = true;
      redisClient = null;
    });

    await redisClient.connect();
    console.log('[Redis] Connected to Redis server');

    return redisClient;
  } catch (error) {
    console.warn('[Redis] Connection failed, using in-memory fallback:', error);
    useInMemoryFallback = true;
    redisClient = null;
    return null;
  }
}

/**
 * Clean up expired entries from in-memory store
 */
function cleanupInMemoryStore(): void {
  const now = Date.now();
  for (const [key, value] of inMemoryStore.entries()) {
    if (value.expiresAt < now) {
      inMemoryStore.delete(key);
    }
  }
}

/**
 * Store OAuth state with expiry (default 10 minutes)
 */
export interface OAuthState {
  code_verifier: string;
  clerk_id: string;
  agent_id: string;
  mcp_url: string;
  provider: string;
  client_id: string;
}

export async function storeOAuthState(
  state: string,
  data: OAuthState,
  ttl: number = 600 // 10 minutes
): Promise<void> {
  const client = await getRedisClient();
  const key = `oauth:${state}`;

  if (client) {
    // Use Redis
    await client.set(key, JSON.stringify(data), {
      EX: ttl
    });
  } else {
    // Use in-memory fallback
    const expiresAt = Date.now() + (ttl * 1000);
    inMemoryStore.set(key, { data: JSON.stringify(data), expiresAt });
    cleanupInMemoryStore();
  }
}

/**
 * Retrieve OAuth state
 */
export async function getOAuthState(state: string): Promise<OAuthState | null> {
  const client = await getRedisClient();
  const key = `oauth:${state}`;

  if (client) {
    // Use Redis
    const data = await client.get(key);
    if (!data) {
      return null;
    }
    return JSON.parse(data) as OAuthState;
  } else {
    // Use in-memory fallback
    cleanupInMemoryStore();
    const entry = inMemoryStore.get(key);

    if (!entry) {
      return null;
    }

    // Check if expired
    if (entry.expiresAt < Date.now()) {
      inMemoryStore.delete(key);
      return null;
    }

    return JSON.parse(entry.data) as OAuthState;
  }
}

/**
 * Delete OAuth state (after successful token exchange)
 */
export async function deleteOAuthState(state: string): Promise<void> {
  const client = await getRedisClient();
  const key = `oauth:${state}`;

  if (client) {
    // Use Redis
    await client.del(key);
  } else {
    // Use in-memory fallback
    inMemoryStore.delete(key);
  }
}

/**
 * Close Redis connection (for cleanup)
 */
export async function closeRedis(): Promise<void> {
  if (redisClient) {
    await redisClient.quit();
    redisClient = null;
  }
}
