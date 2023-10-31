from django.contrib import admin
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path, include

from usuario.urls import usuarioRouters
from bolao.urls import bolaoRouters


admin.site.site_header = 'Starbet.space'
admin.site.site_title = 'Starbet.space, a sua plataforma de bolão!'
admin.site.index_title = 'Starbet.space, a sua plataforma de bolão!'


urlpatterns = [
    path('admin/', admin.site.urls),
    # Usuário
    path('api/v1/usuario/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/usuario/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/v1/usuario/', include(usuarioRouters.urls)),
    path('api/v1/bolao/', include(bolaoRouters.urls)),
    path('api/v1/core/', include('core.urls'))
]
