"""
Authentication forms.
This module provides forms for authentication and user management.
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
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
