from django.contrib import admin

from .models import AnalogColor
from .models import AnalogRecipe


class AnalogColorAdmin(admin.ModelAdmin):
    fields = [
       'name',
       'image_url',
       'medium',
       'body',
       'brandname',
       'glossiness',
       'lightfastness',
       'series',
       'tinting',
       'transparency',
       '_recipe_gloss',
       '_recipe_matte',
       '_recipe_medium',
       '_recipe_oil',
       '_recipe_thinner',
       '_recipe_water',
    ]


admin.site.register(AnalogColor, AnalogColorAdmin)
admin.site.register(AnalogRecipe)
