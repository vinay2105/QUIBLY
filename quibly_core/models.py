
from django.db import models
from django.contrib.auth.models import User

class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tweets')
    content = models.TextField(max_length=280, blank=True)
    caption = models.CharField(max_length=200, blank=True)  # ✅ new
    image = models.ImageField(upload_to='tweet_images/', blank=True, null=True)  # ✅ new
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_tweets', blank=True)

    def total_likes(self):
        return self.likes.count()
    

class Comment(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} on {self.tweet.id}'
    

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    dob = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', default='https://res.cloudinary.com/dykmgthqj/image/upload/vXXXXXXXX/default.jpg')

    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)


    def __str__(self):
        return self.user.username
    

from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"To: {self.recipient.username} - {self.message}"

