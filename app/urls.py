from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
                  path('api/', include(router.urls)),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
