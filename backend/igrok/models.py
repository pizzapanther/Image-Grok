from urlparse import urlparse

from django.conf import settings
from django import http

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api.blobstore import create_gs_key
from google.appengine.api import memcache

import cloudstorage as gcs

SECURE_URL = True

if settings.DEV:
  SECURE_URL = False
  
class Thumbnail (ndb.Model):
  file = ndb.StringProperty(required=True)
  original = ndb.StringProperty(required=True)
  
  width = ndb.IntegerProperty(required=True)
  height = ndb.IntegerProperty(required=True)
  crop = ndb.BooleanProperty(default=False)
  created = ndb.DateTimeProperty(auto_now_add=True)
  
  location = settings.GOOGLE_CLOUD_STORAGE_BUCKET
  
  def gs_key (self):
    return create_gs_key("/gs" + self.location + "/" + self.file)
    
  def url (self):
    return images.get_serving_url(self.gs_key(), secure_url=SECURE_URL)
    
  @classmethod
  def create (cls, content, url, width, height, crop):
    urlobj = urlparse(url)
    
    count = 0
    while 1:
      new_name = urlobj.hostname + urlobj.path + '.' + str(count)
      new_path = cls.location + "/" + new_name
      
      try:
        gcs.stat(new_path)
        
      except gcs.NotFoundError:
        break
        
      else:
        count += 1
        
      if count > 20:
        return http.HttpResponse(
          'Too Many Images With The Same Name',
          status=400,
          content_type='text/plain'
        )
        
    kwargs = {
      'width': width,
      'height': height,
      'allow_stretch': False,
    }
    
    if crop:
      kwargs['crop_to_fit'] = True
      kwargs['crop_offset_y'] = 0.25
      
    thumbnail = images.resize(content, **kwargs)
    
    gcs_file = gcs.open(new_path, mode='w')
    gcs_file.write(thumbnail)
    gcs_file.close()
    
    thumbnail = cls(
      file=new_name,
      original=url,
      width=width,
      height=height,
      crop=crop,
    )
    thumbnail.put()
    
    return thumbnail
    