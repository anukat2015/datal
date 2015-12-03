from django.conf.urls import patterns, include
from django.conf import settings
from django.conf.urls.static import static

from rest_framework import routers
from djangoplugins.utils import include_plugins

from core.plugins import DatalPluginPoint
from api.rest.datastreams import DataStreamViewSet
from api.rest.datasets import DataSetViewSet
from api.rest.visualizations import VisualizationViewSet

router = routers.DefaultRouter()
router.register(r'datastreams', DataStreamViewSet, base_name='datastreams')
router.register(r'datasets', DataSetViewSet, base_name='datasets')
router.register(r'visualizations', VisualizationViewSet, base_name='visualizations')

# Implemento los routers que tenga el plugin
plugins = DatalPluginPoint.get_plugins()
for plugin in plugins:
    if plugin.is_active() and hasattr(plugin, 'api_routers'):
        for router_list in plugin.api_routers:
            router.register(router_list[0], router_list[1], base_name=router_list[2])


urlpatterns = patterns('',
    (r'^', include_plugins(DatalPluginPoint, urls='api_urls')),
    (r'^api/v1/', include(router.urls)),
)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
