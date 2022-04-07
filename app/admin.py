from django.contrib import admin
from .models import *


class SourceTrackInline(admin.TabularInline):
    model = SourceTrack


class SourceFileAdmin(admin.ModelAdmin):
    list_filter = []
    search_fields = (
        'filename',
    )
    list_per_page = 200
    inlines = [SourceTrackInline, ]
    list_display = ("id", "filename", "path_on_dropbox",
                    "is_youtube",
                    "file_url",
                    "youtube_link", "youtube_fetch_task",
                    )


class SourceTrackAdmin(admin.ModelAdmin):
    list_filter = []
    search_fields = (
        'user',
    )
    list_per_page = 200
    inlines = []
    list_display = ("id", "user", "artist",
                    "tone", "bpm",
                    "title", "date_created", "source_file",
                    "url",
                    "youtube_link", "youtube_fetch_task"
                    )


class StaticMixAdmin(admin.ModelAdmin):
    list_filter = []
    search_fields = (
        'filename', 'owner'
    )
    list_per_page = 200
    inlines = []
    list_display = ("id", "owner", "celery_id", "source_track", "vocals",
                    "piano", "drums",
                    "bass", "other",
                    "status", "file_url", "filename", "path_on_dropbox",
                    "date_created", "date_finished",
                    "artist", "title", "source_url"
                    )

    def owner(self, obj):
        return obj.source_track.user


class YTAudioDownloadTaskAdmin(admin.ModelAdmin):
    list_filter = ['status', ]
    search_fields = (
        'celery_id', 'status',
    )
    inlines = []
    list_display = ("id", "celery_id", "status", "date_finished",)


class DynamicMixAdmin(admin.ModelAdmin):
    list_filter = []
    search_fields = (
        'vocals_url', 'piano_url', 'bass_url', 'drums_url', 'other_url',
    )
    list_per_page = 200
    inlines = []
    list_display = ("id", "owner", "source_track",
                    "artist", "title", "status", "date_created", "date_finished",
                    "folder_path_on_dropbox", "celery_id", "source_url", "vocals_url", "piano_url",
                    "bass_url", "drums_url", "other_url",
                    )

    def owner(self, obj):
        return obj.source_track.user


# Register your models here.
admin.site.register(SourceFile, SourceFileAdmin)
admin.site.register(SourceTrack, SourceTrackAdmin)
admin.site.register(StaticMix, StaticMixAdmin)
admin.site.register(DynamicMix, DynamicMixAdmin)
admin.site.register(YTAudioDownloadTask, YTAudioDownloadTaskAdmin)
