from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, send_from_directory, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, \
    EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, Post
from app.email import send_password_reset_email
from flask import g 
from app.forms import SearchForm 
from app.forms import EditPostForm 
from app.forms import MessageForm 
from app.models import Message, Friend
import re 
from app.models import Article1
import json 
from flask import jsonify 
import os 
from PIL import Image, ImageOps, ImageDraw, UnidentifiedImageError
import string
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit() 
        
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search(): 
    form = SearchForm() 
    posts=[] 
    searchuser=None
    allpost=Post.query.all() 
    if form.validate_on_submit(): 
       user=User.query.filter_by(username=form.body.data).first() 
       if user:
          searchuser=user
       else:
          for sp in allpost:
            sp1=str(sp)
            sp2=re.sub(r'\W+', ' ', sp1) 
            testdata=sp2.split()
            for data in testdata: 
               data1=data.casefold()
               if form.body.data==data1:
                  posts.append(sp) 
    return render_template('searchtext.html', title='Results', form=form,posts=posts,posttype=True,user=searchuser)

@app.route('/messages/<recipient>',methods=['GET', 'POST'])
@login_required
def messages(recipient): 
    user = User.query.filter_by(username=recipient).first_or_404()
    current_user.last_message_read_time = datetime.utcnow() 
    db.session.commit() 
    form = MessageForm()
    if form.validate_on_submit(): 
        msg = Message(author=current_user, recipient=user, body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('messages',recipient=user.username))
    page = request.args.get('page', 1, type=int)
    messages1 = Message.query.filter_by(author=current_user,recipient=user) 
    messages2 = Message.query.filter_by(author=user,recipient=current_user) 
    messages=messages1.union(messages2).order_by(Message.timestamp.desc()).paginate( page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('messages',recipient=user.username, page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('messages',recipient=user.username, page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html',form=form, messages=messages.items, next_url=next_url, prev_url=prev_url,recipient=recipient) 
    
@app.route('/deletemessage/<message>/<recipientname>')
@login_required 
def deletemessage(message,recipientname): 
     msg=Message.query.filter_by(body=message,author=current_user).first_or_404() 
     user = User.query.filter_by(username=recipientname).first_or_404()
     db.session.delete(msg) 
     db.session.commit() 
     flash('Deleted!')
     return redirect(url_for('messages',recipient=user.username))

@app.route('/editmessage/<message>/<recipientname>',methods=['GET', 'POST'])
@login_required 
def editmessage(message,recipientname): 
    post1=Message.query.filter_by(body=message,author=current_user).first_or_404() 
    postid=post1.id 
    posttime=post1.timestamp
    user = User.query.filter_by(username=recipientname).first_or_404()
    form = MessageForm()
    if form.validate_on_submit(): 
        db.session.delete(post1) 
        msg = Message(author=current_user, recipient=user, body=form.message.data, id=postid, timestamp=posttime)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been edited.')
        return redirect(url_for('messages',recipient=user.username)) 
    elif request.method == 'GET':
        form.message.data=message
    return render_template('send_message.html', title='Edit Message', form=form, recipient=recipientname) 
    
@app.route('/show_notif') 
@login_required 
def show_notif():
    notificationlist=current_user.new_messages_show() 
    if not notificationlist:
      flash('No notification!') 
    return render_template('notif.html',notiflist=notificationlist) 
  
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('index')) 
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Home', form=form,posts=posts.items,user=user, next_url=next_url, prev_url=prev_url,posttype=True) 
    
@app.route('/deletepost/<post>')
@login_required 
def deletepost(post): 
     post1=Post.query.filter_by(body=post,author=current_user).first_or_404()
     db.session.delete(post1) 
     db.session.commit() 
     flash('Deleted!')
     return redirect(url_for('index')) 
     
@app.route('/editpost/<post>',methods=['GET', 'POST'])
@login_required 
def editpost(post): 
    form=EditPostForm(post) 
    if form.validate_on_submit(): 
      post1=Post.query.filter_by(body=post,author=current_user).first_or_404() 
      postid=post1.id 
      posttime=post1.timestamp
      db.session.delete(post1) 
      db.session.commit()
      post2=Post(id=postid,body=form.post.data,timestamp=posttime,author=current_user) 
      db.session.add(post2)
      db.session.commit() 
      flash('Edited!')
      return redirect(url_for('index')) 
    elif request.method == 'GET':
      form.post.data=post
    return render_template('editpost.html',title='Edit Post',form=form)
    
@app.route('/explore')
@login_required
def explore(): 
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Explore',user=user, posts=posts.items,next_url=next_url, prev_url=prev_url,posttype=True)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index')) 
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)  
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404() 
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,next_url=next_url, prev_url=prev_url, form=form,posttype=True) 
    
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data 
        db.session.commit() 
        a="/app/uploads/"+current_user.username+".jpg" 
        b="/app/static"+current_user.username+".png" 
        imgfile=form.file.data
        if imgfile: 
          if os.path.exists(a):
              os.remove(a)
          if os.path.exists(b):
              os.remove(b) 
          imgfile.save(os.path.join('app/uploads',current_user.username+".jpg")) 
          size = (128, 128)
          mask = Image.new('L', size, 0)
          draw = ImageDraw.Draw(mask) 
          draw.ellipse((0, 0) + size, fill=255) 
          try:
             im = Image.open(os.path.join('app/uploads',current_user.username+".jpg")) 
          except UnidentifiedImageError: 
             flash('Please try another image!')
          output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
          output.putalpha(mask)
          output.save(os.path.join('app/static',current_user.username+".png"))
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.route('/delete_profile', methods=['GET', 'POST'])
@login_required
def delete_profile(): 
  user=User.query.filter_by(username=current_user.username).first() 
  posts=Post.query.filter_by(user_id=user.id).all()
  messages1 = Message.query.filter_by(author=current_user) 
  messages2 = Message.query.filter_by(recipient=current_user) 
  messages=messages1.union(messages2).all() 
  for msg in messages:
    db.session.delete(msg) 
    db.session.commit()
    db.session.commit() 
  for post in posts:
    db.session.delete(post) 
    db.session.commit() 
  db.session.delete(user) 
  db.session.commit() 
  flash('Your account has been deleted')
  return redirect(url_for('login'))
  
  
@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash('You are not following {}.'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))
        
@app.route('/addfriend/<username>', methods=['POST'])
@login_required
def addfriend(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot friend yourself!')
            return redirect(url_for('user', username=username))
        frnd1 = Friend(friendname=username, author=current_user, recipient=user)
        db.session.add(frnd1) 
        frnd2 = Friend(friendname=username, author=user, recipient=current_user) 
        db.session.add(frnd2) 
        frnd3 = Friend(friendname=current_user.username, author=user, recipient=current_user) 
        db.session.add(frnd3) 
        frnd4 = Friend(friendname=current_user.username, author=current_user, recipient=user) 
        db.session.add(frnd4)
        db.session.commit()
        flash('You are now friends with {}!'.format(username))
        return redirect(url_for('listfriend'))
    else:
        return redirect(url_for('index')) 
        
@app.route('/unfriend/<username>', methods=['POST'])
@login_required
def unfriend(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash('User {} not found.'.format(username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfriend yourself!')
            return redirect(url_for('user', username=username))
        frnd1=Friend.query.filter_by(friendname=username,author=current_user,recipient=user).first()
        if frnd1:
          db.session.delete(frnd1) 
        else:
          pass
        frnd2=Friend.query.filter_by(friendname=current_user.username,author=current_user,recipient=user).first() 
        if frnd2:
          db.session.delete(frnd2) 
        else:
          pass
        frnd3=Friend.query.filter_by(friendname=username,author=user,recipient=current_user).first() 
        if frnd3:
          db.session.delete(frnd3)
        else:
          pass
        frnd4=Friend.query.filter_by(friendname=current_user.username,author=user,recipient=current_user).first() 
        if frnd4:
          db.session.delete(frnd4)
        else:
          pass
        db.session.commit()
        flash('You unfriended {}!'.format(username))
        return redirect(url_for('listfriend'))
    else:
        return redirect(url_for('index')) 
   
@app.route('/listfriend')
@login_required
def listfriend():     
    form=EmptyForm()
    friend1=Friend.query.filter_by(author=current_user)
    friend2=Friend.query.filter_by(recipient=current_user)
    friends=friend1.union(friend2).all() 
    if not friends:
      flash('You dont have any friend on this site') 
      return redirect(url_for('index')) 
    userslist=[]
    for i in friends:
      users=User.query.filter_by(username=i.friendname).all() 
      for u in users:
        userslist.append(u) 
    friendlist = list(dict.fromkeys(userslist))
    return render_template('friends.html',messages=friendlist,form=form) 

@app.route('/stories')  
def stories():
  return render_template('stories.html')
    
@app.route('/article_1',methods=['GET','POST']) 
def article_1():
  form=PostForm() 
  if form.validate_on_submit(): 
      if current_user.is_authenticated: 
        comment = Article1(body=form.post.data,author=current_user) 
        db.session.add(comment)
        db.session.commit() 
      else: 
         flash('Can you register before? Please?')
         return redirect(url_for('register'))
  posts = Article1.query.all()
  return render_template('telegrambotai.html',form=form,posts=posts,title='Article')