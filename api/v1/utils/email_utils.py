#!/usr/bin/python3
""" Email helper functions """
from flask_mail import Message
from flask import url_for
from config import mail


def send_password_reset_email(user_email, reset_token):
    """Sends a password reset email to the user."""
    msg = Message('Password Reset Request',
                  recipients=[user_email])
    # msg.body = f"To reset your password, visit the following api endpoint with your reset token: {url_for('app_views.reset_password', token=reset_token, _external=True)}"
    msg.body = f"To reset your password, visit the following API endpoint with your reset token: " \
            f"{url_for('app_views.reset_password', token=reset_token, _external=True)}. " \
            "The request body must contain a 'new_password' field with the new password. " \
            "Example format: {'new_password': 'your_new_password'}."

    try:
        mail.send(msg)
        result = "Password reset email sent."
    except Exception as e:
        result = f"Error sending email: {e}"
    return result
