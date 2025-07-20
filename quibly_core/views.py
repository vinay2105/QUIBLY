from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
import random

from .models import Tweet, UserProfile
from .forms import RegisterForm, TweetForm, UserProfileForm


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            otp = str(random.randint(100000, 999999))

            # Save registration data and OTP in session
            request.session['reg_data'] = form.cleaned_data
            request.session['otp'] = otp

            # Send OTP to email
            send_mail(
                subject='Your OTP for Quibly Registration',
                message=f'Your OTP is: {otp}',
                from_email='noreply@quibly.com',
                recipient_list=[form.cleaned_data['email']],
                fail_silently=False,
            )

            return redirect('verify_otp')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def verify_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('otp')
        reg_data = request.session.get('reg_data')

        if entered_otp == session_otp:
            # Create user
            user = User.objects.create_user(
                username=reg_data['username'],
                email=reg_data['email'],
                password=reg_data['password1']
            )

            # Create empty profile
            UserProfile.objects.create(user=user)

            login(request, user)

            # Clear session
            request.session.pop('otp')
            request.session.pop('reg_data')

            messages.success(request, "Registration complete!")
            return redirect('edit_profile')  # Redirect to profile completion
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect('verify_otp')

    return render(request, 'verify_otp.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home_view(request):
    tweets = Tweet.objects.all().order_by('-created_at')
    return render(request, 'home.html', {'tweets': tweets})


@login_required
def profile_view(request):
    return render(request, 'profile.html')


@login_required
def post_tweet_view(request):
    if request.method == 'POST':
        form = TweetForm(request.POST)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            return redirect('home')
    else:
        form = TweetForm()
    return render(request, 'post_tweet.html', {'form': form})


def edit_profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})

from .models import Tweet, Comment
from .forms import CommentForm
from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def like_tweet_view(request, tweet_id):
    tweet = Tweet.objects.get(id=tweet_id)
    if request.user in tweet.likes.all():
        tweet.likes.remove(request.user)
    else:
        tweet.likes.add(request.user)
    return redirect('home')

@login_required
def comment_tweet_view(request, tweet_id):
    tweet = Tweet.objects.get(id=tweet_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.tweet = tweet
            comment.save()
    return redirect('home')

@login_required
def view_tweet_view(request, tweet_id):
    tweet = Tweet.objects.get(id=tweet_id)
    comments = tweet.comments.all().order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.tweet = tweet
            comment.save()
            return redirect('view_tweet', tweet_id=tweet.id)
    else:
        form = CommentForm()

    return render(request, 'view_tweet.html', {'tweet': tweet, 'form': form, 'comments': comments})





