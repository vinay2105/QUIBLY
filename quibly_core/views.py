from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
import random

from .models import Tweet, UserProfile
from .forms import RegisterForm, TweetForm, UserProfileForm


import random
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from .forms import RegisterForm

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            otp = str(random.randint(100000, 999999))

            # Save data to session (but store passwords safely)
            request.session['reg_username'] = form.cleaned_data['username']
            request.session['reg_email'] = form.cleaned_data['email']
            request.session['reg_password'] = form.cleaned_data['password1']
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

        if not reg_data or not session_otp:
            messages.error(request, "Session expired. Please register again.")
            return redirect('register')

        if entered_otp == session_otp:
            # Create user
            user = User.objects.create_user(
                username=reg_data['username'],
                email=reg_data['email'],
                password=reg_data['password1']
            )

            # Create empty profile
            UserProfile.objects.create(user=user)

            # Log the user in
            login(request, user)

            # Clear the whole session
            request.session.flush()

            messages.success(request, "Registration complete!")
            return redirect('edit_profile')  # Redirect to profile completion
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'verify_otp.html')

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


from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            user = User.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp

            send_mail(
                'Your OTP to reset password - Quibly',
                f'Your OTP is: {otp}',
                'noreply@quibly.com',
                [email],
                fail_silently=False
            )
            messages.success(request, 'OTP sent to your email.')
            return redirect('verify_reset_otp')
        except User.DoesNotExist:
            messages.error(request, 'No account with this email.')
    return render(request, 'forgot_password.html')


def verify_reset_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        if entered_otp == request.session.get('reset_otp'):
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP')
            return redirect('verify_reset_otp')
    return render(request, 'verify_reset_otp.html')


def reset_password_view(request):
    if request.method == 'POST':
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        if password1 == password2:
            email = request.session.get('reset_email')
            try:
                user = User.objects.get(email=email)
                user.password = make_password(password1)
                user.save()

                # Clear session
                request.session.pop('reset_email')
                request.session.pop('reset_otp')

                messages.success(request, 'Password reset successful.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Something went wrong.')
        else:
            messages.error(request, 'Passwords do not match.')
    return render(request, 'reset_password.html')

from django.shortcuts import get_object_or_404
from .models import Notification

@login_required
def follow_toggle_view(request, username):
    target_user = get_object_or_404(User, username=username)
    profile = request.user.profile

    if profile != target_user.profile:
        if target_user.profile in profile.following.all():
            profile.following.remove(target_user.profile)
        else:
            profile.following.add(target_user.profile)

    return redirect('public_profile', username=username)

    # Notification
    Notification.objects.create(
        recipient=target_user,
        message=f"@{request.user.username} followed you."
    )

    return redirect('public_profile', username=username)


def public_profile_view(request, username):
    target_user = get_object_or_404(User, username=username)
    is_following = False

    if request.user.is_authenticated:
        is_following = target_user.profile in request.user.profile.following.all()

    return render(request, 'public_profile.html', {
        'target_user': target_user,
        'is_following': is_following
    })

def notifications_view(request):
    notifications = request.user.notifications.order_by('-timestamp')
    unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, 'notifications.html', {'notifications': notifications})

def like_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    user = request.user

    if user in tweet.likes.all():
        tweet.likes.remove(user)
    else:
        tweet.likes.add(user)
        
        # 🔔 Notification for tweet owner
        if tweet.user != user:  # don’t notify yourself
            Notification.objects.create(
                recipient=tweet.user,
                message=f"@{user.username} liked your tweet."
            )

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def comment_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(user=request.user, tweet=tweet, content=content)

            # 🔔 Notification to tweet owner
            if tweet.user != request.user:
                Notification.objects.create(
                    recipient=tweet.user,
                    message=f"@{request.user.username} commented on your tweet."
                )

    return redirect('view_tweet', tweet_id=tweet_id)






