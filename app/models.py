from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import db, login
import json 
import os
import sys 
import time 
import requests
followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic') 
    comments= db.relationship('Article1', backref='author', lazy='dynamic') 
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic') 
    messages_sent = db.relationship('Message', foreign_keys='Message.sender_id',backref='author', lazy='dynamic')
    messages_received = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)
    requests = db.relationship('Friend', foreign_keys='Friend.request_id',backref='author', lazy='dynamic')
    receives = db.relationship('Friend', foreign_keys='Friend.receive_id', backref='recipient', lazy='dynamic')
    def __repr__(self):
        return '<User {}>'.format(self.username) 
        
    def new_messages(self): 
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).count()
       
        
    def new_messages_show(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        m= Message.query.filter_by(recipient=self).filter(Message.timestamp > last_read_time).all() 
        notiflist=[] 
        for n in m:
          notiflist.append(n) 
        return notiflist 
    
          
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8') 
      
    def add_notification(self, name, data):
        prevnoti=self.notifications.filter_by(name=name).all() 
        if prevnoti:
          for p in prevnoti:
            db.session.delete(p)
        n = Notification(name=name, payload_json=json.dumps(data),user=self)
        db.session.add(n) 
        return n        
            
    def is_friend(self,user,curr): 
        f1=Friend.query.filter_by(friendname=user.username,author=curr,recipient=user).first()
        f2=Friend.query.filter_by(friendname=user.username,author=user,recipient=curr).first()
        f3=Friend.query.filter_by(friendname=curr.username,author=curr,recipient=user).first()
        f4=Friend.query.filter_by(friendname=curr.username,author=user,recipient=curr).first()
        if f1:
          return True
        else:
          return False 
        if f2:
          return True
        else:
          return False 
        if f3:
          return True
        else:
          return False 
        if f4:
          return True
        else:
          return False 
          
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id) 
        

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Post(db.Model): 
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body) 
   
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body) 

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    receive_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    friendname = db.Column(db.String(140)) 
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Friend {}>'.format(self.friendname)     

class Article1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post {}>'.format(self.body) 
    