from django.shortcuts import render
from django.http import JsonResponse


def terms_of_service(request):
    return render(request, 'terms_of_service.html')


def index(request):
    return render(request, 'index.html')


def search(request, query):
    return render(request, 'search.html', {
        "query": query
    })


def api(request, lead):
    return JsonResponse({
        'id': lead,
        'name': 'Spacely Sprockets',
        'contact': 'Cosmo Spacely'
    })
