##################################################################################################
# Copyright (c) 2012 Brett Dixon
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in 
# the Software without restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the 
# Software, and to permit persons to whom the Software is furnished to do so, 
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all 
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS 
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR 
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER 
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
##################################################################################################


from django.contrib import admin

from frog.models import Gallery, Image, Video, Tag

class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'owner', 'security')


class ImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'guid', 'author', 'thumbnail_tag')


class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'guid', 'author', 'thumbnail_tag')


class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    list_filter = ('artist',)



admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Tag, TagAdmin)