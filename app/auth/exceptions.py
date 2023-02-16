from enum import Enum

from app.core.exceptions import ApiException
from app.core.translation import gettext as _


class AuthException(ApiException, Enum):
    email_already_exists = _("User with this email already exists")
    invalid_credentials = _("Either email or password is invalid")
    user_not_found = _("User is not found")
    user_is_inactive = _("User is inactive")
    user_not_superuser = _("User is not superuser")

    invalid_access_token = _("Access token is invalid")
    expired_access_token = _("Access token is expired")
    invalid_refresh_token = _("Refresh token is invalid")
    expired_refresh_token = _("Refresh token is expired")
    invalid_password_reset_token = _("Password reset token is invalid")
    expired_password_reset_token = _("Password reset token is expired")
    invalid_email_verification_token = _("Email verification token is invalid")
    expired_email_verification_token = _("Email verification token is expired")
    invalid_oauth2_token = _("Social login token is invalid")
    expired_oauth2_token = _("Social login token is expired")
