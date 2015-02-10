from django.conf.urls import include, url
#from django.contrib import admin

urlpatterns = [
  url(r'^grok/(.*?)/(.*)$', 'igrok.views.grok', name='grok'),
  #url(r'^blog/', include('blog.urls')),
  
  #url(r'^admin/', include(admin.site.urls)),
]
