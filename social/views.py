
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from .models import Profile, Post, Like, Comment, Follow, Notification


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')

        if not all([username, email, password, confirm]):
            return render(request, 'register.html',
                          {'error': 'All fields are required.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html',
                          {'error': 'Username already exists.'})

        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'register.html',
                          {'error': 'Email already exists.'})

        if password != confirm:
            return render(request, 'register.html',
                          {'error': 'Passwords do not match.'})

        if len(password) < 8:
            return render(request, 'register.html',
                          {'error': 'Password must contain at least 8 characters.'})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        Profile.objects.get_or_create(user=user)
        login(request, user)
        return redirect('home')

    return render(request, 'register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = User.objects.filter(email__iexact=identifier).first()
        username = user.username if user else identifier

        authenticated_user = authenticate(
            request, username=username, password=password
        )

        if authenticated_user:
            login(request, authenticated_user)
            return redirect('home')

        return render(request, 'login.html',
                      {'error': 'Invalid username/email or password.'})

    return render(request, 'login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('login')


@login_required
def home_view(request):
    posts = Post.objects.select_related('user').prefetch_related(
        'like_set', 'comment_set__user'
    ).all()

    return render(request, 'index.html', {'posts': posts})


@login_required
@require_POST
def create_post(request):
    content = request.POST.get('content', '').strip()
    image = request.FILES.get('image')

    if not content and not image:
        return JsonResponse(
            {'success': False, 'error': 'Write something or upload an image.'},
            status=400
        )

    if image:
        if image.size > 5 * 1024 * 1024:
            return JsonResponse(
                {'success': False, 'error': 'Image must be under 5 MB.'},
                status=400
            )
        if image.content_type not in ['image/jpeg', 'image/png', 'image/webp']:
            return JsonResponse(
                {'success': False, 'error': 'Only JPG, PNG and WEBP images are allowed.'},
                status=400
            )

    post = Post.objects.create(
        user=request.user,
        content=content,
        image=image
    )

    return JsonResponse({
        'success': True,
        'message': 'Post published successfully!',
        'post_id': post.id
    })


@login_required
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(
        user=request.user, post=post
    )

    if created and post.user != request.user:
        Notification.objects.create(
            recipient=post.user,
            sender=request.user,
            post=post,
            notification_type='like'
        )
    elif not created:
        like.delete()

    return JsonResponse({
        'success': True,
        'liked': created,
        'count': post.like_set.count()
    })


@login_required
@require_POST
def comment_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    text = request.POST.get('text', '').strip()

    if not text:
        return JsonResponse(
            {'success': False, 'error': 'Comment cannot be empty.'},
            status=400
        )

    comment = Comment.objects.create(
        user=request.user, post=post, text=text
    )

    if post.user != request.user:
        Notification.objects.create(
            recipient=post.user,
            sender=request.user,
            post=post,
            notification_type='comment'
        )

    return JsonResponse({
        'success': True,
        'username': request.user.username,
        'text': comment.text,
        'count': post.comment_set.count()
    })


@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.user != request.user:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    post.delete()
    return JsonResponse({'success': True})


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user)

    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'posts': posts
    })


@login_required
def explore_view(request):
    users = User.objects.exclude(id=request.user.id).annotate(
        followers_count=Count('followers', distinct=True)
    ).order_by('-date_joined')

    return render(request, 'explore.html', {'users': users})


@login_required
@require_POST
def follow_user(request, username):
    target = get_object_or_404(User, username=username)

    if target == request.user:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=target
    )

    if created:
        Notification.objects.create(
            recipient=target,
            sender=request.user,
            notification_type='follow'
        )
    else:
        follow.delete()

    return JsonResponse({
        'success': True,
        'following': created,
        'followers': target.followers.count()
    })


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post')

    notifications.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {
        'notifications': notifications
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.user != request.user:
        return JsonResponse({'error': 'Permission denied.'}, status=403)

    comment.delete()
    return JsonResponse({'success': True})
