/**
 * Frontend Logger for Next.js
 * Sends logs to backend /api/logs endpoint
 * Falls back to console if backend unavailable
 */

class FrontendLogger {
  private endpoint = 'http://localhost:8003/api/logs';

  /**
   * Send log to backend
   * Non-blocking - errors are swallowed to avoid breaking app
   */
  private async sendLog(level: string, message: string, data?: any) {
    try {
      await fetch(this.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          timestamp: new Date().toISOString(),
          level,
          message,
          data: data || {},
          userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : '',
          url: typeof window !== 'undefined' ? window.location.href : ''
        })
      });
    } catch (err) {
      // Silently fail - logging should never break the app
      // Fallback to console for dev visibility
      if (process.env.NODE_ENV === 'development') {
        console.warn('Logger backend unavailable:', err);
      }
    }
  }

  /**
   * Log error with optional Error object
   */
  error(message: string, error?: Error | any, data?: any) {
    // Always log to console for dev visibility
    console.error(message, error, data);

    // Send to backend
    this.sendLog('ERROR', message, {
      error: error?.message || String(error),
      stack: error?.stack,
      ...data
    });
  }

  /**
   * Log warning
   */
  warning(message: string, data?: any) {
    console.warn(message, data);
    this.sendLog('WARNING', message, data);
  }

  /**
   * Log info (only send important events to backend)
   */
  info(message: string, data?: any) {
    console.log(message, data);
    this.sendLog('INFO', message, data);
  }

  /**
   * Debug logs - only console, not sent to backend
   */
  debug(message: string, data?: any) {
    if (process.env.NODE_ENV === 'development') {
      console.log('[DEBUG]', message, data);
    }
  }
}

// Export singleton instance
export const logger = new FrontendLogger();
