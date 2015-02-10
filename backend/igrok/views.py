import time
import json
import logging
import hashlib
from urlparse import urlparse

from django import http
from django.conf import settings
from django.views.decorators.cache import cache_page

from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import images

import cloudstorage as gcs

from .models import Thumbnail

def working_key (url, width, height):
  key = json.dumps([url, width, height])
  key = 'img-resize:' + hashlib.sha1(key).hexdigest()
  return key
  
def create_image (url, width, height):
  added = memcache.add(working_key(url, width, height), 'working', time=60)
  
  if added:
    result = urlfetch.fetch(url)
    
    if result.status_code == 200:
      urlobj = urlparse(url)
      
      count = 0
      while 1:
        new_name = urlobj.hostname + urlobj.path + '.' + str(count)
        new_path = Thumbnail.location + "/" + new_name
        
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
          
      thumbnail = images.resize(
        result.content,
        width=width,
        height=height,
        #output_encoding=images.PNG,
        #crop_to_fit=True,
        allow_stretch=False,
        #crop_offset_y=0.25,
      )
      
      gcs_file = gcs.open(new_path, mode='w')
      gcs_file.write(thumbnail)
      gcs_file.close()
      
      thumbnail = Thumbnail(
        file=new_name,
        original=url,
        width=width,
        height=height
      )
      thumbnail.put()
      
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
      ).get()
      
      if thumb:
        break
        
      else:
        time.sleep(0.01)
        
  if settings.DEV:
    return http.HttpResponseRedirect(thumb.url())
    
  return http.HttpResponsePermanentRedirect(thumb.url())
  
@cache_page(60 * 5)
def grok (request, protocol, img_url):
  img_url = protocol + '://' + img_url
  
  size = request.GET.get('size', '')
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
    
  thumb = Thumbnail.query(
    Thumbnail.original == img_url,
    Thumbnail.width == width,
    Thumbnail.height == height
  ).get()
  
  if thumb:
    if settings.DEV:
      return http.HttpResponseRedirect(thumb.url())
      
    return http.HttpResponsePermanentRedirect(thumb.url())
    
  return create_image(img_url, width, height)
  