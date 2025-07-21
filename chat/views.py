from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Thread, Message
from quibly_core.models import UserProfile
from django.db.models import Q

@login_required
def chat_home(request):
    # Get all threads involving the current user
    threads = Thread.objects.filter(users=request.user)
    return render(request, 'chat/chat_home.html', {'threads': threads})

@login_required
def chat_detail(request, username):
    other_user = get_object_or_404(User, username=username)

    current_profile = request.user.profile
    other_profile = other_user.profile
    if other_profile not in current_profile.following.all() or current_profile not in other_profile.following.all():
        return redirect('chat_home')

    thread = Thread.objects.filter(users=request.user).filter(users=other_user).first()
    if not thread:
        thread = Thread.objects.create()
        thread.users.add(request.user, other_user)

    if request.method == 'POST':
        msg = request.POST.get('message')
        if msg:
            Message.objects.create(thread=thread, sender=request.user, text=msg)
            return redirect('chat_detail', username=other_user.username)

    chat_messages = thread.messages.all().order_by('timestamp')
    return render(
        request,
        'chat/chat_detail.html',
        {
            'thread': thread,
            'chat_messages': chat_messages,
            'other_user': other_user,
        }
    )
