from django.db import models
from django.utils.timezone import now

# Create your models here.
# -*- coding: utf-8 -*-

class Book(models.Model):
    title = models.CharField("本のタイトル", max_length=50)
    author = models.CharField("筆者の名前", max_length=20)
    image = models.ImageField("表紙")
    register_day = models.DateTimeField(verbose_name="登録日時", auto_now_add=True, null=True)


class Likephrase(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    page = models.IntegerField("ページ数", null=True)
    like_phrase = models.TextField("好きなフレーズ", null=True)
    comment = models.TextField('コメント', null=True)
