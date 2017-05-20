from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, validators
# from wtforms.widgets import TextArea

class UserForm(FlaskForm): #this is inheriting from FlaskForm class
  username = StringField('Username', [validators.Length(min=1)])
  email = StringField('Email', [validators.Length(min=5, max=35)])
  first_name = StringField('First Name', [validators.Length(min=1)])
  last_name = StringField('Last Name', [validators.Length(min=1)])

class MessageForm(FlaskForm):
  msg_text = TextAreaField('Message', render_kw={"rows": 10, "cols": 80}, validators = [validators.Length(min=20, max=100)])