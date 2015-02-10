from django.conf import settings

from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api.blobstore import create_gs_key
from google.appengine.api import memcache

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
    