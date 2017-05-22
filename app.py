from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_modus import Modus
from forms import UserForm, MessageForm
from sqlalchemy.exc import IntegrityError
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgres://localhost/userdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
modus = Modus(app)

class User(db.Model):
  __tablename__ = "users"

  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.Text, unique=True, nullable=False)
  email = db.Column(db.Text, unique=True, nullable=False)
  first_name = db.Column(db.Text)
  last_name = db.Column(db.Text)
  messages = db.relationship('Message', backref='user', lazy='dynamic')

  def __init__(self, username, email, first_name, last_name):
    self.username = username
    self.email = email
    self.first_name = first_name
    self.last_name = last_name

  def __repr__(self):
    return "This user's username is {}, email is {}, first name is {}, and last name is {}".format(self.username, self.email, self.first_name, self.last_name)

class Message(db.Model):
  __tablename__ = "messages"

  id = db.Column(db.Integer, primary_key=True)
  msg_text = db.Column(db.String(100), nullable=False)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id')) #has to be primary key here

  def __init__(self, msg_text, user_id):
    self.msg_text = msg_text
    self.user_id = user_id

  def __repr__(self):
    return "The message is: {}".format(self.msg_text)

@app.route('/')
def root():
  return redirect(url_for('index'))

@app.route('/users')
def index():
  ##############HOW COULD I LIMIT THIS FLASH MESSAGE TO ONLY SHOW FOR THE INITIAL PAGE LOAD???#################
  # flash("Welcome to the site!")
  users = User.query.all()
  return render_template('index.html', users = users)

@app.route('/users/<int:user_id>', methods=["GET", "PATCH", "DELETE"])
def show(user_id):
  selected_user = User.query.get_or_404(user_id)
  form = UserForm(request.form, obj=selected_user)

  #if updating the user & form validates...
  if request.method == b'PATCH' and form.validate():
    try: 
      form.populate_obj(selected_user)
      db.session.add(selected_user)
      db.session.commit()
      flash("You edited this user.")
      return redirect(url_for('show', user_id = selected_user.id))
    #if violates unique field for username/email
    except IntegrityError as e:
      if (str(e.orig.pgerror).find('username_key') != -1):
        flash("Please enter a different username. This user already exists.")
      else:
        flash("Please enter a different email. This email already exists.")
      db.session.rollback()
      return render_template('edit.html', user=selected_user, form=form)
  #if form isn't validating...
  elif request.method == b'PATCH':
      return render_template('edit.html', user=selected_user, form=form)

  #if deleting the user
  if request.method == b'DELETE':
    db.session.delete(selected_user)
    db.session.commit()
    flash("You deleted the user: " + selected_user.username)
    return redirect(url_for('index'))

  #else show info about the user
  ######IF WANTED TO LOOP OVER VALUES IN INSTANCE#########
  user_dict = dict((col, getattr(selected_user, col)) for col in selected_user.__table__.columns.keys())
  return render_template('show.html', user=selected_user, user_dict = user_dict) 

@app.route('/users/<int:user_id>/edit', methods=['GET'])
def edit(user_id):
  selected_user = User.query.get(user_id)
  form = UserForm(request.form, obj=selected_user)

  return render_template('edit.html', user=selected_user, form=form)

@app.route('/users/new', methods=['GET', 'POST'])
def new():
  form = UserForm(request.form)

  if request.method == 'POST' and form.validate():
    try:
      new_user = User(form.username.data, form.email.data, form.first_name.data, form.last_name.data)
      db.session.add(new_user)
      db.session.commit()
      flash("You added the user: " + new_user.username)
      return redirect(url_for('index'))

    #if violates unique field for username/email
    except IntegrityError as e:
      if (str(e.orig.pgerror).find('username_key') != -1):
        flash("Please enter a different username. This user already exists.")
      else:
        flash("Please enter a different email. This email already exists.")

  return render_template('new.html', form=form)


#MESSAGES

@app.route('/users/<int:user_id>/messages')
def msg_index(user_id):
  #list the messages  
  user = User.query.get(user_id)
  messages = user.messages
  return render_template('msgs/index.html', messages=messages, user=user)

@app.route('/users/<int:user_id>/messages/new', methods=["GET", "POST"])
def msg_new(user_id):
  user = User.query.get(user_id)
  msg_form = MessageForm(request.form)

  if request.method == 'POST' and msg_form.validate():
    new_msg = Message(msg_form.msg_text.data, user_id)
    db.session.add(new_msg)
    db.session.commit()
    flash('You added the message: "' + msg_form.msg_text.data + '"')
    return redirect(url_for('msg_index', user_id=user_id))

  return render_template('msgs/new.html', user=user, form=msg_form)

@app.route('/users/<int:user_id>/messages/<int:msg_id>', methods=['PATCH', 'DELETE'])
def msg_show(user_id,msg_id):
  user = User.query.get_or_404(user_id)
  selected_message = Message.query.get_or_404(msg_id)
  form = MessageForm(request.form, obj=selected_message)

  #if updating the user & form validates...
  if request.method == b'PATCH' and form.validate():
      form.populate_obj(selected_message)
      db.session.add(selected_message)
      db.session.commit()
      flash('You edited the message. "' + selected_message.msg_text + '"')
      return redirect(url_for('msg_index', user_id= user.id))

  #if form isn't validating...
  elif request.method == b'PATCH':
      return render_template('msgs/edit.html', user_id=user.id, msg_id=selected_message.id, form=form)

  #delete message
  if request.method == b'DELETE':
    db.session.delete(selected_message)
    db.session.commit()
    flash('You deleted the message: "' + selected_message.msg_text + '"')
    return redirect(url_for('msg_index', user_id=user.id))

@app.route('/users/<int:user_id>/messages/<int:msg_id>/edit')
def msg_edit(user_id, msg_id):
  user = User.query.get(user_id)
  selected_message = Message.query.get(msg_id)
  msg_form = MessageForm(request.form, obj=selected_message)

  return render_template('msgs/edit.html', user=user, message=selected_message, form=msg_form)

# If we are in production, make sure we DO NOT use the debug mode
if os.environ.get('ENV') == 'production':
  debug = False
else:
  debug = True

if __name__ == '__main__':
  app.run(debug=debug)
