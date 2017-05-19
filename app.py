from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_modus import Modus
import os

app = Flask(__name__)
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

@app.route('/users', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    new_user = User(request.form['username'], request.form['email'], request.form['first_name'], request.form['last_name'])
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index'))

  users = User.query.all()
  return render_template('index.html', users = users)

@app.route('/users/<int:user_id>', methods=["GET", "PATCH", "DELETE"])
def show(user_id):
  selected_user = User.query.get_or_404(user_id)

  #if updating the user
  if request.method == b'PATCH':
    selected_user.username = request.form['username']
    selected_user.email = request.form['email']
    selected_user.first_name = request.form['first_name']
    selected_user.last_name = request.form['last_name']
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

  return render_template('edit.html', user=selected_user)

@app.route('/users/new')
def new():
  return render_template('new.html')


#MESSAGES

@app.route('/users/<int:user_id>/messages', methods=["GET", "POST"])
def msg_index(user_id):
  if request.method == "POST":
    new_msg = Message(request.form['msg_text'], user_id)
    db.session.add(new_msg)
    db.session.commit()
    return redirect(url_for('msg_index', user_id=user_id))

  #else just list the messages  
  user = User.query.get(user_id)
  messages = user.messages
  return render_template('msgs/index.html', messages=messages, user=user)

@app.route('/users/<int:user_id>/messages/new')
def msg_new(user_id):
  user = User.query.get(user_id)
  return render_template('msgs/new.html', user=user)

@app.route('/users/<int:user_id>/messages/<int:msg_id>', methods=['PATCH', 'DELETE'])
def msg_show(user_id,msg_id):
  user = User.query.get(user_id)
  message = Message.query.get(msg_id)

  #update message
  if request.method == b'PATCH':
    message.msg_text = request.form['msg_text']
    db.session.add(message)
    db.session.commit()
    return redirect(url_for('msg_index', user_id = user.id))

  #delete message
  if request.method == b'DELETE':
    db.session.delete(message)
    db.session.commit()
    return redirect(url_for('msg_index', user_id=user.id))

  #else, show the message
  return render_template('msgs/show.html', user=user, message=message)

@app.route('/users/<int:user_id>/messages/<int:msg_id>/edit')
def msg_edit(user_id, msg_id):
  user = User.query.get(user_id)
  message = Message.query.get(msg_id)

  return render_template('msgs/edit.html', user=user, message=message)

# If we are in production, make sure we DO NOT use the debug mode
if os.environ.get('ENV') == 'production':
  debug = False
else:
  debug = True

if __name__ == '__main__':
  app.run(debug=debug)
