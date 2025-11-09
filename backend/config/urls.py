from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse  # 👈 For backend test page

# Simple root route for testing
def home(request):
    return HttpResponse("<h1>✅ Backend is running successfully!</h1>")

urlpatterns = [
    path('', home),  # test route
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),  # 👈 main API
    path('predictor/', include('predictor.urls')),  # 👈 predictor app (if exists)
]
