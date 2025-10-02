/**
 * Config utilities for Phase 4: FastAPI Bridge Integration
 * Handles the new merged config format from FastAPI
 */

export interface MergedConfigValue {
  default: any;
  user_override: any;
  current: any;
  is_overridden: boolean;
}

/**
 * Extract the current value from a config field
 * Handles both old format (raw values) and new format (merged objects from FastAPI)
 *
 * @param value - The value to extract (can be raw value or MergedConfigValue object)
 * @returns The current value to display
 */
export function extractCurrentValue(value: any): any {
  // Check if this is the new FastAPI merged format
  if (value && typeof value === 'object' && 'current' in value) {
    return value.current;
  }

  // Fall back to raw value (old format, backward compatible)
  return value;
}

/**
 * Check if a config field is overridden by the user
 *
 * @param value - The config field value
 * @returns true if the field has a user override
 */
export function isFieldOverridden(value: any): boolean {
  if (value && typeof value === 'object' && 'is_overridden' in value) {
    return value.is_overridden;
  }
  return false;
}

/**
 * Get the default value for a config field
 *
 * @param value - The config field value
 * @returns The default value
 */
export function getDefaultValue(value: any): any {
  if (value && typeof value === 'object' && 'default' in value) {
    return value.default;
  }
  return value;
}

/**
 * Get the user override value for a config field
 *
 * @param value - The config field value
 * @returns The user override value, or null if not overridden
 */
export function getUserOverride(value: any): any | null {
  if (value && typeof value === 'object' && 'user_override' in value) {
    return value.user_override;
  }
  return null;
}
