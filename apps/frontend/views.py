from django.shortcuts import render

# Create your views here.
def frontend_index(request):
    # data = list(profiles.values())
    # return HttpResponse(f'<pre>sjdgfkj</pre>')
    return render(request, 'frontend/index.html')