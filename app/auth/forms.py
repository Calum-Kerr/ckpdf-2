"""
Authentication forms.
This module provides forms for authentication and user management.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError


class ChangePasswordForm(FlaskForm):
    """
    Form for changing a user's password.
    """
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])

    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])

    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])

    submit = SubmitField('Change Password')

    def validate_new_password(self, field):
        """
        Validate that the new password is different from the current password.

        Args:
            field: The new_password field.

        Raises:
            ValidationError: If the new password is the same as the current password.
        """
        if field.data == self.current_password.data:
            raise ValidationError('New password must be different from current password')


class RequestPasswordResetForm(FlaskForm):
    """
    Form for requesting a password reset.
    """
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])

    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    """
    Form for resetting a password.
    """
    password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])

    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('password', message='Passwords must match')
    ])

    submit = SubmitField('Reset Password')
