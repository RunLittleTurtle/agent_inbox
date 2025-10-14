"""
Google Workspace API Executor - TEMPLATE
Handles direct Google API calls with OAuth credentials.

CUSTOMIZATION REQUIRED:
1. Replace {SERVICE_NAME} with your Google API service (e.g., 'people', 'gmail', 'calendar')
2. Replace {API_VERSION} with your API version (e.g., 'v1', 'v3')
3. Update SCOPES with your required scopes (must match config.py)
4. Implement domain-specific methods (replace example_method_*)

Google API Reference:
- Calendar API: https://developers.google.com/calendar/api/v3/reference
- People API (Contacts): https://developers.google.com/people/api/rest
- Gmail API: https://developers.google.com/gmail/api/reference/rest
- Drive API: https://developers.google.com/drive/api/v3/reference
"""
import logging
from typing import Dict, Any, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleWorkspaceExecutor:
    """
    Generic Google Workspace API executor.
    Builds authenticated Google API service client.
    """

    # TODO: Update these with your Google API details
    SERVICE_NAME = "{SERVICE_NAME}"  # e.g., 'people', 'gmail', 'calendar', 'drive'
    API_VERSION = "{API_VERSION}"    # e.g., 'v1', 'v3'

    # TODO: Update scopes (must match config.py GOOGLE_OAUTH_SCOPES)
    SCOPES = [
        "https://www.googleapis.com/auth/REPLACE_WITH_YOUR_SCOPE",
    ]

    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize Google Workspace executor with OAuth credentials.

        Args:
            credentials: Dict containing:
                - google_refresh_token: User's OAuth refresh token
                - google_client_id: OAuth app client ID
                - google_client_secret: OAuth app client secret
        """
        logger.info(f"Initializing GoogleWorkspaceExecutor for {self.SERVICE_NAME} API")

        self.credentials = self._build_google_credentials(credentials)
        self.service = self._build_service()

        logger.info(f"GoogleWorkspaceExecutor initialized successfully")

    def _build_google_credentials(self, creds_dict: Dict[str, str]) -> Credentials:
        """
        Build Google OAuth2 Credentials object.

        This method is GENERIC and reusable across all Google APIs.
        Only the SCOPES need to be updated per domain.

        Args:
            creds_dict: Dict with refresh_token, client_id, client_secret

        Returns:
            Google Credentials object ready for API calls
        """
        logger.info("Building Google OAuth2 credentials")

        credentials = Credentials(
            token=None,  # Will be auto-refreshed using refresh_token
            refresh_token=creds_dict['google_refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_dict['google_client_id'],
            client_secret=creds_dict['google_client_secret'],
            scopes=self.SCOPES
        )

        logger.info("Google credentials built successfully")
        return credentials

    def _build_service(self):
        """
        Build Google API service client.

        Returns:
            Google API service object (e.g., calendar service, gmail service, etc.)
        """
        logger.info(f"Building Google {self.SERVICE_NAME} API service (version {self.API_VERSION})")

        try:
            service = build(
                self.SERVICE_NAME,
                self.API_VERSION,
                credentials=self.credentials
            )
            logger.info(f"Google {self.SERVICE_NAME} service built successfully")
            return service
        except Exception as e:
            logger.error(f"Error building Google service: {e}")
            raise

    # ==========================================================================
    # DOMAIN-SPECIFIC METHODS - CUSTOMIZE THESE
    # ==========================================================================
    # TODO: Replace these example methods with your domain-specific implementations
    #
    # EXAMPLES FOR DIFFERENT GOOGLE APIS:
    #
    # --- Google Calendar API ---
    # def list_events(self, calendar_id='primary', max_results=10):
    #     """List calendar events"""
    #     events = self.service.events().list(
    #         calendarId=calendar_id,
    #         maxResults=max_results,
    #         singleEvents=True,
    #         orderBy='startTime'
    #     ).execute()
    #     return events.get('items', [])
    #
    # --- Google Contacts API (People API) ---
    # def list_contacts(self, page_size=50):
    #     """List contacts"""
    #     results = self.service.people().connections().list(
    #         resourceName='people/me',
    #         pageSize=page_size,
    #         personFields='names,emailAddresses,phoneNumbers'
    #     ).execute()
    #     return results.get('connections', [])
    #
    # --- Gmail API ---
    # def list_messages(self, query='', max_results=10):
    #     """List email messages"""
    #     results = self.service.users().messages().list(
    #         userId='me',
    #         q=query,
    #         maxResults=max_results
    #     ).execute()
    #     return results.get('messages', [])
    #
    # --- Google Drive API ---
    # def list_files(self, page_size=10):
    #     """List Drive files"""
    #     results = self.service.files().list(
    #         pageSize=page_size,
    #         fields="nextPageToken, files(id, name, mimeType)"
    #     ).execute()
    #     return results.get('files', [])

    def example_method_list(self, **kwargs) -> List[Dict[str, Any]]:
        """
        TODO: Replace with your domain-specific list method.

        Example: list_contacts(), list_events(), list_messages(), etc.

        Returns:
            List of items from Google API
        """
        raise NotImplementedError(
            "Replace this method with your domain-specific implementation. "
            "See examples in comments above."
        )

    def example_method_get(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """
        TODO: Replace with your domain-specific get method.

        Example: get_contact(contact_id), get_event(event_id), get_message(message_id), etc.

        Args:
            item_id: ID of item to retrieve

        Returns:
            Single item from Google API
        """
        raise NotImplementedError(
            "Replace this method with your domain-specific implementation. "
            "See examples in comments above."
        )

    def example_method_search(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """
        TODO: Replace with your domain-specific search method.

        Example: search_contacts(query), search_messages(query), etc.

        Args:
            query: Search query string

        Returns:
            List of matching items from Google API
        """
        raise NotImplementedError(
            "Replace this method with your domain-specific implementation. "
            "See examples in comments above."
        )

    # ==========================================================================
    # ERROR HANDLING HELPER (REUSABLE)
    # ==========================================================================

    def _handle_api_error(self, error: Exception, operation: str) -> str:
        """
        Generic error handler for Google API calls.
        This method is REUSABLE across all Google APIs.

        Args:
            error: Exception raised by Google API
            operation: Description of operation that failed

        Returns:
            User-friendly error message
        """
        if isinstance(error, HttpError):
            logger.error(f"Google API error during {operation}: {error}")
            return f"Google API error: {error.resp.status} - {error.resp.reason}"
        else:
            logger.error(f"Unexpected error during {operation}: {error}")
            return f"Unexpected error: {str(error)}"
