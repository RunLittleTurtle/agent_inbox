/**
 * Interrupt Format Adapter
 *
 * Converts between different interrupt formats to ensure compatibility
 * with existing agents that use custom interrupt schemas.
 */

import { HumanInterrupt, HumanInterruptConfig, ActionRequest } from "../types";

// Legacy interrupt format used by our calendar agent and other existing agents
export interface LegacyInterrupt {
  type: string;
  message?: string;
  instructions?: string;
  booking_details?: Record<string, any>;
  [key: string]: any; // Allow additional properties
}

/**
 * Detects if an interrupt is in legacy format
 */
export function isLegacyInterrupt(interrupt: any): interrupt is LegacyInterrupt {
  return (
    typeof interrupt === "object" &&
    interrupt !== null &&
    typeof interrupt.type === "string" &&
    !interrupt.action_request // No action_request means it's legacy format
  );
}

/**
 * Converts legacy interrupt format to Agent Inbox compatible format
 */
export function convertLegacyInterrupt(legacy: LegacyInterrupt): HumanInterrupt {
  // Default configuration - can be customized based on interrupt type
  const defaultConfig: HumanInterruptConfig = {
    allow_ignore: false,
    allow_respond: true,
    allow_edit: true,
    allow_accept: true,
  };

  // Handle different legacy interrupt types
  switch (legacy.type) {
    case "booking_approval": {
      // Calendar booking approval interrupt
      const actionRequest: ActionRequest = {
        action: "calendar_booking_approval",
        args: legacy.booking_details || {},
      };

      return {
        action_request: actionRequest,
        config: {
          allow_ignore: false, // Booking shouldn't be ignored
          allow_respond: true, // Allow feedback
          allow_edit: true,    // Allow modifications
          allow_accept: true,  // Allow approval
        },
        description: legacy.message || legacy.instructions || "Approval Required",
      };
    }

    case "email_approval": {
      // Email approval interrupt
      const actionRequest: ActionRequest = {
        action: "email_approval",
        args: legacy.email_details || {},
      };

      return {
        action_request: actionRequest,
        config: defaultConfig,
        description: legacy.message || "Email approval required",
      };
    }

    default: {
      // Generic conversion for unknown types
      const actionRequest: ActionRequest = {
        action: legacy.type,
        args: extractArgsFromLegacy(legacy),
      };

      return {
        action_request: actionRequest,
        config: defaultConfig,
        description: legacy.message || legacy.instructions || `${legacy.type} approval required`,
      };
    }
  }
}

/**
 * Extracts arguments from legacy interrupt format
 */
function extractArgsFromLegacy(legacy: LegacyInterrupt): Record<string, any> {
  const args: Record<string, any> = {};

  // Extract known fields that should be in args
  const knownFields = ['booking_details', 'email_details', 'data', 'details'];

  for (const field of knownFields) {
    if (legacy[field] && typeof legacy[field] === 'object') {
      Object.assign(args, legacy[field]);
    }
  }

  // If no known fields found, include all non-metadata fields
  if (Object.keys(args).length === 0) {
    const metadataFields = ['type', 'message', 'instructions'];
    for (const [key, value] of Object.entries(legacy)) {
      if (!metadataFields.includes(key)) {
        args[key] = value;
      }
    }
  }

  return args;
}

/**
 * Processes interrupts array, converting legacy formats to Agent Inbox format
 */
export function processInterrupts(interrupts: any[]): HumanInterrupt[] {
  return interrupts.map(interrupt => {
    if (isLegacyInterrupt(interrupt)) {
      return convertLegacyInterrupt(interrupt);
    }

    // Already in correct format or unknown format
    return interrupt as HumanInterrupt;
  });
}

/**
 * Converts Agent Inbox response back to legacy format if needed
 */
export function convertResponseToLegacy(
  response: any,
  originalInterruptType?: string
): any {
  // For now, just return the response as-is
  // This can be enhanced if agents need specific response formats
  return response;
}
