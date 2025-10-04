/**
 * Generic Credential Validation Utility
 *
 * Validates any type of credential (API keys, tokens, URLs, secrets)
 * to prevent common copy-paste errors and encoding issues.
 */

export interface ValidationResult {
  isValid: boolean;
  error?: string;
  warning?: string;
}

export type CredentialType =
  | 'api_key'
  | 'url'
  | 'token'
  | 'secret'
  | 'oauth_credential'
  | 'generic';

/**
 * Core validation: Checks for Unicode and masked characters
 * This is the primary issue we need to prevent
 */
function validateCharacterSet(value: string): ValidationResult {
  // Check for Unicode bullet characters (the main problem)
  const bulletPattern = /[•●○◉◎◐◑◒◓◔◕◖◗◘◙◚◛◜◝◞◟◠◡◢◣◤◥◦◧◨◩◪◫◬◭◮◯█▓▒░⬤⬡⬢⬣⬥⬦⬧⬨⬩∙∘]/;
  if (bulletPattern.test(value)) {
    return {
      isValid: false,
      error: "This field contains masked characters (•). Please paste the actual credential, not the masked version from your password manager."
    };
  }

  // Check for repeated asterisks (common masking)
  if (/^\*{5,}$/.test(value)) {
    return {
      isValid: false,
      error: "This appears to be a masked value. Please paste the actual credential."
    };
  }

  // Check for non-ASCII characters (HTTP headers requirement)
  const asciiPattern = /^[\x00-\x7F]*$/;
  if (!asciiPattern.test(value)) {
    return {
      isValid: false,
      error: "This credential contains non-ASCII characters which will cause API errors. Please ensure you copied it correctly."
    };
  }

  return { isValid: true };
}

/**
 * Validation rules for different credential types
 */
const validationRules: Record<CredentialType, (value: string) => ValidationResult> = {
  api_key: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    // API keys should not contain spaces (unless Bearer token format)
    if (value.includes(' ') && !value.startsWith('Bearer ')) {
      return {
        isValid: false,
        error: "API key contains spaces. Please check for copy-paste errors."
      };
    }

    // Warn if suspiciously short
    if (value.length < 20) {
      return {
        isValid: true,
        warning: "This API key seems short. Please verify it's complete."
      };
    }

    return { isValid: true };
  },

  url: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    // Basic URL format check
    try {
      new URL(value);
    } catch {
      return {
        isValid: false,
        error: "Invalid URL format. Please check the URL is complete and correct."
      };
    }

    // Check for common URL issues
    if (value.includes(' ')) {
      return {
        isValid: false,
        error: "URL contains spaces. Please ensure it's copied correctly."
      };
    }

    return { isValid: true };
  },

  token: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    // Tokens generally shouldn't have whitespace
    if (value.trim() !== value) {
      return {
        isValid: false,
        error: "Token has leading or trailing whitespace. Please trim it."
      };
    }

    return { isValid: true };
  },

  secret: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    // Basic secret validation
    if (value.length < 10) {
      return {
        isValid: true,
        warning: "This secret seems short. Please verify it's correct."
      };
    }

    return { isValid: true };
  },

  oauth_credential: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    // OAuth credentials can be various formats, just check character set
    return { isValid: true };
  },

  generic: (value: string) => {
    const charCheck = validateCharacterSet(value);
    if (!charCheck.isValid) return charCheck;

    return { isValid: true };
  }
};

/**
 * Main validation function
 * @param value - The credential value to validate
 * @param type - The type of credential (determines validation rules)
 * @param fieldName - Optional field name for better error messages
 */
export function validateCredential(
  value: string,
  type: CredentialType = 'generic',
  fieldName?: string
): ValidationResult {
  // Empty values are handled by required field validation
  if (!value) {
    return { isValid: true };
  }

  // Sanitize: remove zero-width characters and normalize whitespace
  const sanitized = value
    .replace(/[\u200B\u200C\u200D\uFEFF]/g, '') // Remove zero-width chars
    .replace(/[\r\n]/g, ''); // Remove line breaks

  // Run type-specific validation
  const validator = validationRules[type];
  const result = validator(sanitized);

  // Add field name to error message if provided
  if (!result.isValid && result.error && fieldName) {
    result.error = `${fieldName}: ${result.error}`;
  }

  return result;
}

/**
 * Helper to determine credential type from field key
 */
export function inferCredentialType(fieldKey: string): CredentialType {
  const key = fieldKey.toLowerCase();

  if (key.includes('url') || key.includes('endpoint')) {
    return 'url';
  }
  if (key.includes('api_key') || key.includes('apikey')) {
    return 'api_key';
  }
  if (key.includes('token')) {
    return 'token';
  }
  if (key.includes('secret') || key.includes('client_secret')) {
    return 'oauth_credential';
  }
  if (key.includes('client_id') || key.includes('refresh')) {
    return 'oauth_credential';
  }

  return 'generic';
}

/**
 * Bulk validation for multiple fields
 */
export function validateCredentials(
  fields: Array<{ key: string; value: string; type?: CredentialType }>
): Record<string, ValidationResult> {
  const results: Record<string, ValidationResult> = {};

  for (const field of fields) {
    const type = field.type || inferCredentialType(field.key);
    results[field.key] = validateCredential(field.value, type, field.key);
  }

  return results;
}
