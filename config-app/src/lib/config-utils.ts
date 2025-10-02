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
 * A field is considered overridden when the user override exists AND differs from the Python default
 *
 * @param value - The config field value
 * @returns true if the field has a user override that differs from default
 */
export function isFieldOverridden(value: any): boolean {
  // Check if this is the new FastAPI merged format
  // A field is overridden when user_override exists AND differs from default
  if (value && typeof value === 'object' && 'user_override' in value && 'default' in value) {
    return value.user_override !== null && value.user_override !== value.default;
  }
  // Fall back to false (no override detected)
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

/**
 * Mask sensitive credentials for display
 * Shows first 7 characters + asterisks + last 3 characters
 * Example: "sk-ant-api03-***************AAA"
 *
 * @param value - The credential value to mask
 * @returns Masked credential string, or empty string if invalid
 */
export function maskCredential(value: string | null | undefined): string {
  // Return empty string for null/undefined/empty values
  if (!value || typeof value !== 'string' || value.trim() === '') {
    return '';
  }

  // If value is too short to mask meaningfully (less than 11 chars), just show asterisks
  if (value.length < 11) {
    return '*'.repeat(value.length);
  }

  // Show first 7 chars + asterisks + last 3 chars
  const firstPart = value.substring(0, 7);
  const lastPart = value.substring(value.length - 3);
  const maskedMiddle = '*'.repeat(15); // Always 15 asterisks for consistency

  return `${firstPart}${maskedMiddle}${lastPart}`;
}

/**
 * Check if a value appears to be a masked credential
 * Used to determine if we should unmask on focus
 *
 * @param value - The value to check
 * @returns true if the value looks like a masked credential
 */
export function isMaskedCredential(value: string | null | undefined): boolean {
  if (!value || typeof value !== 'string') {
    return false;
  }
  // Check if it contains the masking pattern (7 chars + asterisks + 3 chars)
  return /^.{7}\*+.{3}$/.test(value);
}
