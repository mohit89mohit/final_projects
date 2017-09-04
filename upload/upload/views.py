# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render ,redirect
from datetime import datetime
from django.utils import timezone
from demoupload.forms import SignUpForm,LoginForm,PostForm,LikeForm,CommentForm
from django.contrib.auth.hashers import make_password,check_password
from demoupload.models import UserModel , SessionToken,PostModel,LikeModel,CommentModel
from imgurpython import ImgurClient
from settings import BASE_DIR

# Create your views here.

def signup_view(request):
     if request.method == "POST":
         form = SignUpForm(request.POST)
         if form.is_valid():
             username = form.cleaned_data['username']
             name = form.cleaned_data['name']
             email = form.cleaned_data['email']
             password = form.cleaned_data['password']
             # save data to database
             user = UserModel(name=name, password=make_password(password), email=email, username=username)
             user.save()
             template_name = 'success.html'
         else:
             template_name = 'fail.html'

     elif request.method == "GET":
         form = SignUpForm()
         template_name = 'signup.html'

     return render(request, template_name, {'form':form})

def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = UserModel.objects.filter(username=username).first()
            if user:
                #compare password
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('/feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    template_name = 'loginfail.html'
            else:
                template_name = 'loginfail.html'
        else:
            template_name = 'loginfail.html'
    elif request.method == "GET":
        #form = LoginForm()
        template_name = 'login.html'
        form = LoginForm()
    else:
        template_name = 'loginfail.html'

    return render(request, template_name, {'form': form})

def feed_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.all().order_by('-created_on')
        for post in posts:
            existing_like = LikeModel.objects.filter(post=post, user=user).first()
            if existing_like:
                post.has_liked = True
        return render(request, 'feed.html', {'posts': posts})
    else:
        return redirect('/login/')

def post_view(request):
    user = check_validation(request)
    if user:
        if request.method == 'GET':
            form = PostForm()
            return render(request,'post.html',{'form':form})
        elif request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()
                path = str(BASE_DIR + "\\" + post.image.url)
                client_id = 'f898fe4db2daebf'
                client_secret = '680cff299e71871090fa211b35dcb23ac0d2b008'
                client = ImgurClient(client_id, client_secret)
                post.image_url = client.upload_from_path(path, anon=True)['link']
                post.save()
                return redirect('/feed/')
        else:
            form = PostForm()
            return render(request, 'post.html', {'form': form})
    else:
        return redirect('/login/')

def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()
            return redirect('/feed/')
    else:
        return redirect('/login/')

def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
    if session:
        return session.user
    else:
        return None






