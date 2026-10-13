from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("healthz", views.healthz),
    path("estudio/", views.studio, name="studio"),
    path("historial/", views.history, name="history"),
    path("trabajos/<int:pk>/", views.job_detail, name="job_detail"),
    path("trabajos/<int:pk>/estado/", views.job_status, name="job_status"),
    path("trabajos/<int:pk>/imagen/<str:kind>/", views.job_media, name="job_media"),
    path("trabajos/<int:pk>/borrar/", views.job_delete, name="job_delete"),
]
