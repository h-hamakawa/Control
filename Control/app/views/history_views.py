from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import Transaction


@login_required
def history_view(request):
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'history.html', {'transactions': transactions})
