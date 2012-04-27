from django.contrib import admin

from models import Gallery, Image, Video, Tag

class GalleryAdmin(admin.ModelAdmin):
    pass


class ImageAdmin(admin.ModelAdmin):
    pass


class VideoAdmin(admin.ModelAdmin):
    pass


class TagAdmin(admin.ModelAdmin):
    pass



admin.site.register(Gallery, GalleryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Tag, TagAdmin)