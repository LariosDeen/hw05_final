from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm


NUMBER_OF_POSTS: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    template = 'posts/index.html'
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    template = 'posts/group_list.html'
    return render(request, template, context)


def profile(request, username):
    prof_author = get_object_or_404(User, username=username)
    posts_counter = prof_author.posts.count()
    post_list = prof_author.posts.all()
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = Follow.objects.filter(
        user=request.user.id,
        author=prof_author.id
    ).exists()
    context = {
        'prof_author': prof_author,
        'posts_counter': posts_counter,
        'page_obj': page_obj,
        'following': following,
    }
    template = 'posts/profile.html'
    return render(request, template, context)


def post_detail(request, post_id):
    one_post = get_object_or_404(Post, id=post_id)
    one_post_author = one_post.author
    posts_counter = one_post_author.posts.count()
    group_name = one_post.group
    form = CommentForm()
    comments = one_post.comments.filter(post=post_id)
    template = 'posts/post_detail.html'
    context = {
        'one_post': one_post,
        'posts_counter': posts_counter,
        'group_name': group_name,
        'username': one_post_author,
        'post_id': post_id,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    author = request.user
    template = 'posts/create_post.html'
    context = {
        'form': form,
    }
    if not form.is_valid():
        return render(request, template, context)
    post = form.save(commit=False)
    post.author = author
    post.save()
    return redirect('posts:profile', author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    is_edit = True
    template = 'posts/create_post.html'
    context = {
        'form': form,
        'is_edit': is_edit,
    }
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


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/follow.html'
    content = {
        'page_obj': page_obj,
    }
    return render(request, template, content)


@login_required
def profile_follow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    follow_obj = Follow.objects.filter(
        user=user_obj,
        author=author_obj
    )
    if not follow_obj.exists() and author_obj != user_obj:
        Follow.objects.create(user=user_obj, author=author_obj)
    return redirect('posts:profile', username=author_obj.username)


@login_required
def profile_unfollow(request, username):
    author_obj = get_object_or_404(User, username=username)
    user_obj = request.user
    follow_obj = Follow.objects.filter(
        user=user_obj,
        author=author_obj
    )
    if follow_obj.exists():
        follow_obj.delete()
    return redirect('posts:profile', username=author_obj.username)
