# quibly_core/views.py
import random
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Tweet, UserProfile, Comment, Notification
from .forms import RegisterForm, TweetForm, UserProfileForm, CommentForm


# -------------------------
# AUTH & REGISTRATION (OTP)
# -------------------------
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            otp = f"{random.randint(100000, 999999)}"
            reg_data = {
                'username': form.cleaned_data['username'],
                'email':    form.cleaned_data['email'],
                'password': form.cleaned_data['password1'],
            }
            request.session['reg_data'] = reg_data
            request.session['otp'] = otp
            request.session.set_expiry(600)  # 10 minutes

            send_mail(
                subject='Your OTP for Quibly Registration',
                message=f'Your OTP is: {otp}',
                from_email='noreply@quibly.com',
                recipient_list=[reg_data['email']],
                fail_silently=False,
            )
            return redirect('verify_otp')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


@transaction.atomic
def verify_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        session_otp = request.session.get('otp')
        reg_data    = request.session.get('reg_data')

        if not reg_data or not session_otp:
            messages.error(request, "Session expired. Please register again.")
            return redirect('register')

        if entered_otp != session_otp:
            messages.error(request, "Invalid OTP. Please try again.")
            return render(request, 'verify_otp.html')

        user = User.objects.create_user(
            username=reg_data['username'],
            email=reg_data['email'],
            password=reg_data['password']
        )
        UserProfile.objects.create(user=user)

        request.session.pop('otp', None)
        request.session.pop('reg_data', None)

        login(request, user)
        messages.success(request, "Registration complete!")
        return redirect('edit_profile')

    return render(request, 'verify_otp.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password.')
        return redirect('login')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# -------------
# CORE PAGES
# -------------
@login_required
def home_view(request):
    tweets = (Tweet.objects
              .select_related('user', 'user__profile')
              .prefetch_related('comments__user', 'likes')
              .order_by('-created_at'))
    return render(request, 'home.html', {'tweets': tweets})


@login_required
def profile_view(request):
    return render(request, 'profile.html')


@login_required
def edit_profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'edit_profile.html', {'form': form})


# -------------
# TWEETS
# -------------
@login_required
def post_tweet_view(request):
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            form.save_m2m()
            return redirect('home')
    else:
        form = TweetForm()
    return render(request, 'post_tweet.html', {'form': form})


@login_required
def view_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    comments = tweet.comments.all().order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.tweet = tweet
            comment.save()

            if tweet.user != request.user:
                Notification.objects.create(
                    recipient=tweet.user,
                    message=f"@{request.user.username} commented on your tweet."
                )
            return redirect('view_tweet', tweet_id=tweet.id)
    else:
        form = CommentForm()

    return render(request, 'view_tweet.html', {'tweet': tweet, 'form': form, 'comments': comments})


@login_required
def delete_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if tweet.user != request.user:
        messages.error(request, "You are not authorized to delete this tweet.")
        return redirect('home')
    tweet.delete()
    messages.success(request, "Tweet deleted successfully.")
    return redirect('profile')


@login_required
def like_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    user = request.user

    if user in tweet.likes.all():
        tweet.likes.remove(user)
    else:
        tweet.likes.add(user)
        if tweet.user != user:
            Notification.objects.create(
                recipient=tweet.user,
                message=f"@{user.username} liked your tweet."
            )

    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def comment_tweet_view(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(user=request.user, tweet=tweet, content=content)
            if tweet.user != request.user:
                Notification.objects.create(
                    recipient=tweet.user,
                    message=f"@{request.user.username} commented on your tweet."
                )
    return redirect('view_tweet', tweet_id=tweet_id)


# -----------------
# FOLLOW / PROFILE
# -----------------
@login_required
def follow_toggle_view(request, username):
    target_user = get_object_or_404(User, username=username)
    me = request.user.profile
    them = target_user.profile

    if me != them:
        if them in me.following.all():
            me.following.remove(them)
        else:
            me.following.add(them)
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


# -----------------
# NOTIFICATIONS
# -----------------
@login_required
def notifications_view(request):
    notes = request.user.notifications.order_by('-timestamp')
    unread_count = notes.filter(is_read=False).count()
    # Mark as read (optional)
    notes.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {
        'notifications': notes,
        'unread_count': unread_count,
    })


# -----------------
# PASSWORD RESET (OTP)
# -----------------
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'No account with this email.')
            return render(request, 'forgot_password.html')

        otp = str(random.randint(100000, 999999))
        request.session['reset_email'] = email
        request.session['reset_otp'] = otp
        request.session.set_expiry(600)

        send_mail(
            'Your OTP to reset password - Quibly',
            f'Your OTP is: {otp}',
            'noreply@quibly.com',
            [email],
            fail_silently=False
        )
        messages.success(request, 'OTP sent to your email.')
        return redirect('verify_reset_otp')

    return render(request, 'forgot_password.html')


def verify_reset_otp_view(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        if entered_otp == request.session.get('reset_otp'):
            return redirect('reset_password')
        messages.error(request, 'Invalid OTP')
        return redirect('verify_reset_otp')
    return render(request, 'verify_reset_otp.html')


def reset_password_view(request):
    if request.method == 'POST':
        p1 = request.POST.get('password1')
        p2 = request.POST.get('password2')
        if p1 == p2:
            email = request.session.get('reset_email')
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, 'Something went wrong.')
                return redirect('forgot_password')

            user.password = make_password(p1)
            user.save()

            request.session.pop('reset_email', None)
            request.session.pop('reset_otp', None)

            messages.success(request, 'Password reset successful.')
            return redirect('login')
        messages.error(request, 'Passwords do not match.')
    return render(request, 'reset_password.html')


# ---------------
# SEARCH USERS
# ---------------
def search_users_view(request):
    query = request.GET.get('q', '').strip()
    users = []
    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(profile__bio__icontains=query)
        ).select_related('profile')
    return render(request, 'search_results.html', {'query': query, 'users': users})







