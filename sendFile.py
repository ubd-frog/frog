import os, tempfile, zipfile
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper


class FixedFileWrapper(FileWrapper):
    def __iter__(self):        
        self.filelike.seek(0)
        return self


def send_file(request, filename, content_type='image/jpeg'):
    """                                                                         
    Send a file through Django without loading the whole file into              
    memory at once. The FileWrapper will turn the file object into an           
    iterator for chunks of 8KB.                                                 
    """
    wrapper = FixedFileWrapper(file(filename, 'rb'))
    response = HttpResponse(wrapper, content_type=content_type)
    response['Content-Length'] = os.path.getsize(filename)
    return response


def send_zipfile(request, fileList):
    """                                                                         
    Create a ZIP file on disk and transmit it in chunks of 8KB,                 
    without loading the whole file into memory. A similar approach can          
    be used for large dynamic PDF files.                                        
    """
    temp = tempfile.TemporaryFile()
    archive = zipfile.ZipFile(temp, 'w', zipfile.ZIP_DEFLATED)
    for artist,files in fileList.iteritems():
        for f in files:
            archive.write(f[0], '%s/%s' % (artist, f[1]))
    archive.close()
    wrapper = FixedFileWrapper(temp)
    response = HttpResponse(wrapper, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=FrogSources.zip'
    response['Content-Length'] = temp.tell()
    temp.seek(0)
    return response