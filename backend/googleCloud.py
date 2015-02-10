import mimetypes
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage

from google.appengine.api.blobstore import create_gs_key
from google.appengine.api import images

import cloudstorage as gcs

__author__ = 'ckopanos@redmob.gr'
__github__ = 'https://github.com/ckopanos/django-google-cloud-storage'

SECURE_URL = True
if settings.DEV:
  SECURE_URL = False
  
class GoogleCloudStorage(Storage):
    def __init__(self, location=None, base_url=None):
        if location is None:
            location = settings.GOOGLE_CLOUD_STORAGE_BUCKET
            
        self.location = location
        
    def _open(self, name, mode='rb'):
        filename = self.location+"/"+name
        gcs_file = gcs.open(filename,mode='r')
        file = ContentFile(gcs_file.read())
        gcs_file.close()
        return file

    def _save(self, name, content):
        filename = self.location+"/"+name
        filename = os.path.normpath(filename)
        type, encoding = mimetypes.guess_type(name)
        gss_file = gcs.open(filename, mode='w', content_type=type)
        content.open()
        gss_file.write(content.read())
        content.close()
        gss_file.close()
        return name

    def delete(self, name):
        filename = self.location+"/"+name
        try:
            gcs.delete(filename)
        except gcs.NotFoundError:
            pass

    def exists(self, name):
        try:
            self.statFile(name)
            return True
        except gcs.NotFoundError:
            return False

    def listdir(self, path=None):
        directories, files = [], []
        bucketContents = gcs.listbucket(self.location,prefix=path)
        for entry in bucketContents:
            filePath = entry.filename
            head, tail = os.path.split(filePath)
            subPath = os.path.join(self.location,path)
            head = head.replace(subPath,'',1)
            if head == "":
                head = None
            if not head and tail:
                files.append(tail)
            if head:
                if not head.startswith("/"):
                    head = "/"+head
                dir = head.split("/")[1]
                if not dir in directories:
                    directories.append(dir)
        return directories, files

    def size(self, name):
        stats = self.statFile(name)
        return stats.st_size

    def accessed_time(self, name):
        raise NotImplementedError

    def created_time(self, name):
        stats = self.statFile(name)
        return stats.st_ctime

    def modified_time(self, name):
        return self.created_time(name)
        
    def gs_key (self, name):
        name = self.gs_name(name)
        return create_gs_key(name)
        
    def gs_name (self, name):
        return "/gs"+self.location+"/"+name
        
    def url(self, name):
        return images.get_serving_url(self.gs_key(name), secure_url=SECURE_URL)
        
    def statFile(self,name):
        filename = self.location+"/"+name
        return gcs.stat(filename)
        