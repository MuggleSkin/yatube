from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ("pk" ,"text", "pub_date", "author") 
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ("text",) 
    # добавляем возможность фильтрации по дате
    list_filter = ("pub_date",)
    empty_value_display = '-пусто-' # это свойство сработает для всех колонок: где пусто - там будет эта строка

admin.site.register(Post, PostAdmin)
