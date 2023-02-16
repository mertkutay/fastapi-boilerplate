from enum import Enum

from app.core.exceptions import ApiException
from app.core.translation import gettext as _


class OAuth2Exception(ApiException, Enum):
    refresh_token_not_supported = _("Refresh token is not supported")
    revoke_token_not_supported = _("Revoke token is not supported")
    access_token_error = _("Error getting access token")
    refresh_token_error = _("Error getting refresh token")
    revoke_token_error = _("Error revoking token")
    id_email_error = _("Error getting id and email information")
