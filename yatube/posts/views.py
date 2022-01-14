from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect


from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


User = get_user_model()


def page_paginator(data, request):
    """функция разделения записей на несколько страниц"""
    post_list = Paginator(data, settings.PAGINATOR_COUNT)
    page_number = request.GET.get('page')

    return post_list.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()

    page_obj = page_paginator(posts, request)

    context = {'page_obj': page_obj}

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'

    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    page_obj = page_paginator(posts, request)

    context = {'group': group,
               'page_obj': page_obj}

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'

    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = page_paginator(posts, request)

    """проверка является ли текущий юзер анонимным или нет"""
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
    else:
        following = False

    context = {'author': author,
               'page_obj': page_obj,
               'count_post_author': author.posts.count(),
               'following': following}

    return render(request, template, context)


@login_required
def add_comment(request, post_id):

    post = get_object_or_404(Post, id=post_id)

    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'

    post = get_object_or_404(Post, id=post_id)
    count_post_author = post.author.posts.count()
    comments = post.comments.all()

    form = CommentForm(request.POST or None)

    context = {'post': post,
               'count_post_author': count_post_author,
               'comments': comments,
               'form': form}
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    form = PostForm(request.POST or None,
                    files=request.FILES or None)

    if form.is_valid():
        saving = form.save(commit=False)
        saving.author = request.user
        saving.save()

        return redirect('posts:profile', request.user)

    context = {'form': form}
    return render(request, template, context)


def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post.id)

    context = {'form': form,
               'is_edit': True}

    return render(request, template, context)


@login_required
def follow_index(request):
    template = 'posts/follow.html'

    """получение авторов на которых подписан авторизованный юзер"""
    followers = request.user.follower.all().values('author')

    """получение постов вышеполученных авторов"""
    posts = Post.objects.filter(author__in=followers)

    page_obj = page_paginator(posts, request)

    context = {'page_obj': page_obj}

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """авторизованный юзер, который подписывается на авторов"""
    login_user = Follow.objects.filter(user=request.user).first()

    if not login_user:
        login_user = Follow.objects.create(user=request.user)

    """автор на которого надо подписаться"""
    add_user = get_object_or_404(User, username=username)

    login_user.author.add(add_user)

    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора"""
    login_user = Follow.objects.filter(user=request.user).first()

    """автор от которого надо отписаться"""
    add_user = get_object_or_404(User, username=username)

    login_user.author.remove(add_user)

    return redirect('posts:profile', username)
