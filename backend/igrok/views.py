import time
import json
import logging
import hashlib

from django import http
from django.conf import settings
from django.views.decorators.cache import cache_page

from google.appengine.api import urlfetch
from google.appengine.api import memcache

from .models import Thumbnail

def working_key (url, width, height, crop):
  key = json.dumps([url, width, height, crop])
  key = 'img-resize:' + hashlib.sha1(key).hexdigest()
  return key
  
def create_image (url, width, height, crop):
  added = memcache.add(working_key(url, width, height, crop), 'working', time=60)
  
  if added:
    result = urlfetch.fetch(url)
    
    if result.status_code == 200:
      thumb = Thumbnail.create(result.content, url, width, height, crop)
      if isinstance(thumb, http.HttpResponse):
        return thumb
        
    else:
      return http.HttpResponse(
        result.content,
        status=result.status_code,
        content_type=result.headers['content-type']
      )
      
  else:
    while 1:
      thumb = Thumbnail.query(
        Thumbnail.original == url,
        Thumbnail.width == width,
        Thumbnail.height == height,
        Thumbnail.crop == crop,
      ).get()
      
      if thumb:
        break
        
      else:
        time.sleep(0.01)
        
  Thumbnail.cache_me(thumb, url, width, height, crop)
  if settings.DEV:
    return http.HttpResponseRedirect(thumb.url())
    
  return http.HttpResponsePermanentRedirect(thumb.url())
  
@cache_page(60 * 5)
def grok (request, protocol, img_url):
  img_url = protocol + '://' + img_url
  
  size = request.GET.get('size', '')
  crop = False
  if request.GET.get('crop', ''):
    crop = True
    
  try:
    width, height = size.split('x')
    width = int(width)
    height = int(height)
    
  except:
    return http.HttpResponse(
      'Invalid Size',
      status=400,
      content_type='text/plain'
    )
    
  cache_key = Thumbnail.cache_key(img_url, width, height, crop)
  thumb = memcache.get(cache_key)
  if thumb:
    logging.info('Cached: {} {} {} {}'.format(img_url, width, height, crop))
    
  else:
    logging.info('Querying: {} {} {} {}'.format(img_url, width, height, crop))
    thumb = Thumbnail.query(
      Thumbnail.original == img_url,
      Thumbnail.width == width,
      Thumbnail.height == height,
      Thumbnail.crop == crop,
    ).get()
    Thumbnail.cache_me(thumb, img_url, width, height, crop)
    
  if thumb:
    if settings.DEV:
      return http.HttpResponseRedirect(thumb.url())
      
    return http.HttpResponsePermanentRedirect(thumb.url())
    
  return create_image(img_url, width, height, crop)
  