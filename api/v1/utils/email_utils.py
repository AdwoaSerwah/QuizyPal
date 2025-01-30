#!/usr/bin/python3
"""
Helper functions for sending password reset emails.

This module contains functions to generate a password reset URL and send
an email with the reset instructions. The email includes a link with a
reset token and instructions on resetting the password.

Main function:
    - `send_password_reset_email(user_email, reset_token)`: Sends an
      email to the user with a password reset link and instructions.
"""
from flask_mail import Message
from flask import url_for
from config import mail


def send_password_reset_email(user_email, reset_token):
    """
    Sends a password reset email to the user.

    Args:
        user_email (str): The user's email address.
        reset_token (str): The token used for password reset.

    Returns:
        str: Message indicating the result of the email sending process.
    """
    msg = Message('Password Reset Request', recipients=[user_email])

    reset_url = url_for(
        'app_views.reset_password', token=reset_token, _external=True
    )

    msg.body = (
        "To reset your password, visit the following API endpoint with "
        "your reset token: "
        f"{reset_url}. The request body must contain a 'new_password' "
        "field with the new password. Example format: "
        "{'new_password': 'your_new_password'}."
    )

    try:
        mail.send(msg)
        result = "Password reset email sent."
    except Exception as e:
        result = f"Error sending email: {e}"
    return result
