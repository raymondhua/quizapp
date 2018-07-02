from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Tournament)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(PlayerProgress)
admin.site.register(Completed)
