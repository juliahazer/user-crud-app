from flask import Flask, render_template, redirect, request, url_for, flash
from forms import UserForm, MessageForm #IMPORT ALL FUNCTIONS WITHIN FORM!!!
from flask_sqlalchemy import SQLAlchemy
from flask_modus import Modus
import os

app = Flask(__name__)
#CSRF protection but i think this does this locally only
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgres://localhost/userdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
modus = Modus(app)

class User(db.Model):
  __tablename__ = "users"

  #creates columns for the table
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
  flash("Welcome!") #add flash message  
  users = User.query.all()
  return render_template('index.html', users = users)

@app.route('/users/<int:user_id>', methods=["GET", 'PATCH', "DELETE"])
def show(user_id):
  selected_user = User.query.get_or_404(user_id)
  form = UserForm(request.form, obj=selected_user)

  #if updating the user
  if request.method == b'PATCH':
    # selected_user.username = request.form['username']
    # selected_user.email = request.form['email']
    # selected_user.first_name = request.form['first_name']
    # selected_user.last_name = request.form['last_name']
    form.populate_obj(selected_user)
    db.session.add(selected_user)
    db.session.commit()
    return redirect(url_for('index'))

  #if deleting the user
  if request.method == b'DELETE':
    db.session.delete(selected_user)
    db.session.commit()
    return redirect(url_for('index'))

  #else show info about the user
  return render_template('show.html', user=selected_user)

@app.route('/users/<int:user_id>/edit')
def edit(user_id):
  selected_user = User.query.get(user_id)
  form = UserForm(obj=selected_user)
  form.populate_obj(selected_user)

  return render_template('edit.html', user=selected_user, form=form)

@app.route('/users/new', methods=['GET', 'POST'])
def new():
  form = UserForm(request.form)

  if request.method == 'POST' and form.validate():
    new_user = User(form.username.data, form.email.data, form.first_name.data, form.last_name.data)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index'))

  return render_template('new.html', form=form)


#MESSAGES

@app.route('/users/<int:user_id>/messages')
def msg_index(user_id):
  # if request.method == "POST":
  #   new_msg = Message(request.form['msg_text'], user_id)
  #   db.session.add(new_msg)
  #   db.session.commit()
  #   return redirect(url_for('msg_index', user_id=user_id))

  #else just list the messages  
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
    return redirect(url_for('msg_index', user_id=user_id))

  return render_template('msgs/new.html', user=user, form=msg_form)

@app.route('/users/<int:user_id>/messages/<int:msg_id>', methods=['GET', 'DELETE'])
def msg_show(user_id,msg_id):
  user = User.query.get(user_id)
  message = Message.query.get(msg_id)

  #delete message
  if request.method == b'DELETE':
    db.session.delete(message)
    db.session.commit()
    return redirect(url_for('msg_index', user_id=user.id))

  #else, show the message
  return render_template('msgs/show.html', user=user, message=message)

@app.route('/users/<int:user_id>/messages/<int:msg_id>/edit', methods=['GET', 'PATCH'])
def msg_edit(user_id, msg_id):
  user = User.query.get(user_id)
  message = Message.query.get(msg_id)
  # msg_form = MessageForm(request.form)

  #update message
  if request.method == b'PATCH':
    message.msg_text = request.form['msg_text']
    db.session.add(message)
    db.session.commit()
    return redirect(url_for('msg_index', user_id = user.id))

  form = MessageForm(obj=message)
  form.populate_obj(message)

  return render_template('msgs/edit.html', user=user, message=message, form=form)

# If we are in production, make sure we DO NOT use the debug mode
if os.environ.get('ENV') == 'production':
  debug = False
else:
  debug = True

if __name__ == '__main__':
  app.run(debug=debug)
