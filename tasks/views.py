from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import TaskForm
from .models import Task

# Create your views here.
def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'GET':
        return render(request, 'signup.html')
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('tasks')
            except IntegrityError:
                return render(request, 'signup.html', {'error_user':"Username already exists"})
        else:
            return render(request, 'signup.html', {'error_passw':"Password do not match"})
    
@login_required
def tasks(request):
    user_tasks = Task.objects.filter(user=request.user, datecompleted__isnull=True).order_by('-created')
    return render(request, 'tasks.html', {'tasks': user_tasks})

@login_required
def tasks_completed(request):
    user_tasks = Task.objects.filter(user=request.user, datecompleted__isnull=False).order_by('-created')
    return render(request, 'tasks.html', {'tasks': user_tasks})

@login_required
def signout(request):
    logout(request)
    return redirect('home')

def signin(request):
    if request.method == 'GET':
        return render(request, 'login.html')
    else:
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'login.html', {'error':"Username or password is incorrect"})
        else:
            login(request, user)
            return redirect('tasks')
                    
@login_required
def create_task(request):
    if request.method == 'POST':
        try:
            form = TaskForm(request.POST)
            if form.is_valid():
                new_task = form.save(commit=False)
                new_task.user = request.user
                new_task.save()
                return redirect('tasks')
        except ValueError:
            return render(request, 'create_task.html', {'form': form, 'error': "Please provide valid data"})
    else:
        form = TaskForm()
    return render(request, 'create_task.html', {'form': form})
        
@login_required(login_url='login')
def task_detail(request, task_id):
    if request.method == 'GET':
        task = get_object_or_404(Task, pk=task_id, user=request.user)
        form = TaskForm(instance=task)
        context = {'task':task, 'form':form} 
        return render(request, 'task_detail.html', context)
    else:
        try:
            task = get_object_or_404(Task, pk=task_id, user=request.user)
            form = TaskForm(request.POST, instance=task)
            form.save()
            return redirect('tasks')
        except:
            context['error'] = "Error updating task"
            return render(request, 'task_detail.html', context)

@login_required(login_url='login')
@require_POST
def complete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    task.datecompleted = timezone.now()
    task.save(update_fields=['datecompleted'])
    return redirect('tasks')

@login_required(login_url='login')
@require_POST        
def delete_task(request, task_id):
    task = get_object_or_404(Task, pk=task_id, user=request.user)
    task.delete()
    return redirect('tasks')