from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def cli_view(request):
    return render(request, 'locker_wall/cli.html')
