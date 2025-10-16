import { v4 as uuidv4 } from 'uuid';

/**
 * Get or create a persistent session GUID
 * Stored in localStorage for frontend use
 */
export function getSessionGuid(): string {
  if (typeof window !== 'undefined') {
    let sessionGuid = localStorage.getItem('session_guid');
    if (!sessionGuid) {
      sessionGuid = uuidv4();
      localStorage.setItem('session_guid', sessionGuid);
    }
    return sessionGuid;
  }
  // fallback if window is undefined (SSR)
  return uuidv4();
}
