from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "VTON Studio · Administración"
admin.site.site_title = "VTON Studio"
admin.site.index_title = "Panel de métricas y gestión"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuenta/", include("accounts.urls")),
    path("", include("tryon.urls")),
]
