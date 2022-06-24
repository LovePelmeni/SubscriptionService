from . import views, healthcheck as health
from django.urls import path

from django.views.decorators.csrf import csrf_exempt
from drf_yasg import views as yasg_views, openapi

from rest_framework import permissions
from . import customer_api
import django.http

app_name = 'main'


urlpatterns = [

    path('get/sub/list/', views.ObtainCatalogSubscriptionAPIView.as_view({'get': 'list'}), name='sub-list'),
    path('get/sub/', views.ObtainCatalogSubscriptionAPIView.as_view({'get': 'retrieve'}), name='sub-retrieve'),

    #custom subscriptions urls:

    path('get/custom/subs/', views.CustomSubscriptionAPIView.as_view({'get': 'list'}), name='custom-subs'),
    path('get/custom/sub/', views.CustomSubscriptionAPIView.as_view({'get': 'retrieve'}), name='custom-sub'),
    path('custom/sub/', views.CustomSubscriptionAPIView.as_view({'post': 'create'}), name='create-custom-sub'),
    path('custom/sub/delete/', views.DeleteSubscription.as_view(), name='delete-custom-sub'),

    path('check/sub/permission/', views.CheckSubPermissionStatus.as_view(), name='check-sub-permission'),

    #activate urls:
    path('get/activate/sub/form/', views.ApplySubscriptionAPIView.as_view({'get': 'retrieve'}), name='get-activate-sub-form'),
    path('activate/sub/', views.ApplySubscriptionAPIView.as_view({'post': 'create'}), name='activate-subscription'),
    path('disactivate/sub/', views.ApplySubscriptionAPIView.as_view({'delete': 'destroy'}),
    name='disactivate-subscription'),

    # purchased subscriptions urls:
    path('get/purchased/subs/', views.ObtainAppliedSubscriptionAPIView.as_view({'get': 'list'}), name='purchased-subs'),
    path('get/purchased/sub/', views.ObtainAppliedSubscriptionAPIView.as_view({'get': 'retrieve'})),

    #healthcheck urls:
    path('healthcheck/application/', lambda request: django.http.HttpResponse(status=200), name='service-healthcheck'),
    path('healthcheck/celery/', health.CeleryHealthCheckAPIView.as_view(), name='celery-healthcheck'),

    path('create/customer/', customer_api.create_customer, name='create-customer'),
    path('delete/customer/', customer_api.delete_customer, name='delete-customer'),

]

api_schema = yasg_views.get_schema_view(
    openapi.Info(
        title='Subscription Service',
        default_version='1.0',
        description='API Service, Part Of the "Web App" Project. Allows to make Subscriptions.',
        contact=openapi.Contact(email='kirklimushin@gmail.com'),
        license=openapi.License(name='BSD License')
        ),
        public=True,
        permission_classes=(permissions.AllowAny,)
    )

openapi_urlpatterns = [
    path('swagger/', api_schema.with_ui('swagger', cache_timeout=0), name='schema-view'),
    path('redoc/', api_schema.with_ui('redoc', cache_timeout=0), name='redoc'),
]
urlpatterns += openapi_urlpatterns





