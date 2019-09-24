from django.shortcuts import render, get_object_or_404
from django.template.response import TemplateResponse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from record.models import Book, Likephrase
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from datetime import datetime, timedelta
import json
import requests
import sys
import os
from . import models
import collections


# Create your views here.

def base(request):

    books = Book.objects.order_by('-register_day')
    paginator = Paginator(books, per_page=3)
    page = request.GET.get('page')
    try:
        books = paginator.page(page)

    except (EmptyPage, PageNotAnInteger):
        books = paginator.page(1)

    return TemplateResponse(request, 'record/base.html',
                            {'books': books,
                             })


# 本の詳細画面
def book_detail(request, book_id):
    books = Book.objects.filter(id=book_id)
    ph = Likephrase.objects.filter(book_id=book_id)
    book_page = Likephrase.objects.values('page').filter(book_id=book_id)

    return TemplateResponse(request, 'record/book_detail.html',
                                     {'books': books,
                                      'phrase': ph,
                                      'book_page': book_page })


def bookshelf(request):

    books = Book.objects.order_by('-register_day')
    paginator = Paginator(books, per_page=9)
    page = request.GET.get('page')
    try:
        books = paginator.page(page)

    except (EmptyPage, PageNotAnInteger):
        books = paginator.page(1)

    return TemplateResponse(request, 'record/bookshelf.html',
                              {'books': books,
                                })


def data(request):
    month = 1
    book_total = 0
    book_count = [0,0,0,0,0,0,0,0,0,0,0,0]


    this_month = datetime.today().month
    last_month = this_month - 1
    while month <= this_month:
        count = Book.objects.filter(register_day__month = month).count()
        book_count[month -1] = count
        book_total += count
        month += 1

    this_month = book_count[this_month - 1]
    last_month = book_count[last_month - 1]

    return TemplateResponse(request, 'record/data.html',
                             {'book_count': book_count,
                              'book_total': book_total,
                              'this_month': this_month,
                              'last_month': last_month})


def profile(request):
    return TemplateResponse(request, 'record/profile.html')


def recommend(request):
    return TemplateResponse(request, 'record/recommend.html')


@csrf_exempt
def webhook(request):
    req = json.loads(request.body)
    # intent_name = req.get('queryResult').get('intent').get('displayName')
    intent_name = req.get('queryResult').get('intent').get('displayName')
    text = req.get('queryResult').get('queryText')
    session_id = req['session']
    list = []

    if intent_name == "Registration":
        fulfillmentMessages = Start()
        return JsonResponse(fulfillmentMessages)

# 　タイトルを入力してコンテキストの情報を取得する
    if intent_name == 'Registration - ChoiceResponse - TitleResponse':
        outputContext = req.get('queryResult').get('outputContexts')[-1]
        context_text = outputContext.get('parameters').get('Process')

# 　コンテキストの名前が登録ならAPIを呼び出して、その情報を元に登録したい本に間違いないか確認
        if context_text == "本棚に追加":
            list = RakutenAPI(request)
            if type(list) == str:

                fulfillmentMessages = {"fulfillmentMessages": [
                        {
                            "payload":
                            {
                                "line": {
                                    "type": "template",
                                    "altText": "test_template",
                                    "template": {
                                        "type": "buttons",
                                        'title': "ERROR!!",
                                        "text": list,
                                        "thumbnailImageUrl" : 'https://cdn.pixabay.com/photo/2016/04/24/13/24/error-1349562__340.png',
                                        "actions": [
                                            {
                                                "type": "message",
                                                "label": "はい",
                                                "text": "はい"
                                            }
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                    }

                return JsonResponse(fulfillmentMessages)



            else:
                fulfillmentMessages = ConfirmBook(list)
                return JsonResponse(fulfillmentMessages)

#  APIで本の情報を取得後、YESならその情報を元にデータ作成(登録の最終ステップ)
    if text == "YES":
        outputContext = req.get('queryResult').get('outputContexts')[-1]
        outputContext_2 = req.get('queryResult').get('outputContexts')[-2]
        context_text = outputContext.get('parameters').get('Process')
        context_text_2 = outputContext_2.get('parameters').get('Process')

        if context_text == "本棚に追加":
            if intent_name == "Registration - ChoiceResponse - TitleResponse - YesResponse":
                list = RakutenAPI(request)
                title = list[0]
                author = list[1]
                image = list[2]
                msg = CheckBook(list)

                if msg == "":
                    book = Book.objects.create(title=title, author=author, image=image)
                    fulfillmentText = {"fulfillmentText": "登録が完了しました"}
                    return JsonResponse(fulfillmentText)
                else:
                    fulfillmentText = {"fulfillmentText": "すでに" + title + "が登録されています"}
                    return JsonResponse(fulfillmentText)

            elif intent_name == "Registration - ChoiceResponse - TitleResponse - NoResponse - AuthorResponse - YesResponse":
                list = RakutenAPI(request)
                title = list[0]
                author = list[1]
                image = list[2]
                msg = CheckBook(list)

                if msg == "":
                    book = Book.objects.create(title=title, author=author, image=image)
                    fulfillmentText = {"fulfillmentText": "登録が完了しました"}
                    return JsonResponse(fulfillmentText)
                else:
                    fulfillmentText = {"fulfillmentText": "すでに" + title + "は登録されています"}
                    return JsonResponse(fulfillmentText)

        elif context_text_2 == "本棚から削除":
            outputContext = req.get('queryResult').get('outputContexts')[-1]
            title = outputContext.get('parameters').get('any')
            Book.objects.filter(title__icontains=title).delete()
            fulfillmentText = {"fulfillmentText": "削除が完了しました"}
            return JsonResponse(fulfillmentText)

# 　タイトルだけでは商品情報が取得できずに著者名を入力する場合
    if intent_name == "Registration - ChoiceResponse - TitleResponse - NoResponse - AuthorResponse":
        outputContext = req.get('queryResult').get('outputContexts')[-1]
        author = outputContext.get('parameters').get('person').get('name')
        list = RakutenAPI(request)
        fulfillmentMessages = ConfirmBook(list)
        return JsonResponse(fulfillmentMessages)



# 　入力したタイトルの情報を取得する(すでに登録済みの本情報)
    if intent_name == 'Registration - AddResponse - Title' or intent_name == "Registration - DeleteResponse - TitleResponse":
        text = req.get('queryResult').get('queryText')
        global book_title
        book_title = text

        search_books = SearchBook(book_title)
        if search_books == "":
            data = collections.OrderedDict()
            data['fulfillmentText'] = "本棚に存在しません"
            data['outputContexts'] = [
            collections.OrderedDict([
                ('name', session_id + '/contexts/registration-addresponse-title-followup'),
                ('lifespanCount', 0)
            ]),
            collections.OrderedDict([
                ('name', session_id + '/contexts/registration-addresponse-followup'),
                ('lifespanCount', 0)
            ]),
    ]
            # return JsonResponse(fulfillmentText)
            return JsonResponse(data)

        else:
            list.append(search_books[1])
            list.append(search_books[2])
            list.append(search_books[3])
            fulfillmentMessages = ConfirmBook(list)
            return JsonResponse(fulfillmentMessages)


# 　好きなフレーズを入力する
    if intent_name == 'Registration - AddResponse - Title - Yes - Page - Phrase':
        outputContext = req.get('queryResult').get('outputContexts')[1]
        judge = outputContext.get('parameters').get('Judge')
        number = outputContext.get('parameters').get('number')
        pk = SearchBook(book_title)
        pk = pk[0]
        text = req.get('queryResult').get('queryText')
        book = get_object_or_404(models.Book, id = pk)
        Likephrase.objects.create(book=book, like_phrase=text, page=number)
        data = collections.OrderedDict()

        data["fulfillmentMessages"] = [
                    {
                      "card": {
                            "title": "登録が完了しました",
                            "subtitle": "続いて好きなフレーズを登録しますか？",
                            "imageUri": 'https://cdn.pixabay.com/photo/2016/06/01/06/26/open-book-1428428__340.jpg',
                            "buttons": [
                                {
                                    "text": "YES",
                                },
                                {
                                    "text": "NO",
                                },
                            ]
                        }
                    }
                ]
        data['outputContexts'] = [
        collections.OrderedDict([
            ('name', session_id + '/contexts/registration-addresponse-title-yes-followup'),
            ('lifespanCount', 5)
        ]),
        ]
        return JsonResponse(data)

# 　入力された情報をもとに、APIを実行し本の情報を取得する
def RakutenAPI(request):
    URL = 'https://app.rakuten.co.jp/services/api/BooksBook/Search/20170404'
    APPLICATION_ID = os.environ["APPLICATION_ID"]
    req = json.loads(request.body)
    intent_name = req.get('queryResult').get('intent').get('displayName')
    outputContext = req.get('queryResult').get('outputContexts')[-1]
    title = outputContext.get('parameters').get('any')
    context_text = outputContext.get('parameters').get('Judge')

    if context_text == "NO" or intent_name == "Registration - ChoiceResponse - TitleResponse - NoResponse - AuthorResponse - YesResponse":
        outputContext = req.get('queryResult').get('outputContexts')[1]
        title = outputContext.get('parameters').get('any')
        author = outputContext.get('parameters').get('person').get('name')

        parameters = {
        'applicationId': APPLICATION_ID,
        'title': title,
        'author': author,
        'outOfStockFlag': 1,
        }
    else:
        parameters = {
            'applicationId': APPLICATION_ID,
            'title': title,
            'outOfStockFlag': 1,
        }
        # NOのステップに進んでから再度本を表示したとき、textは著者名になっている
        # textの値がYESかNOかを前のステップで取得してNOならauthorありで　YESならauthorなし

    r = requests.get(URL, params=parameters)

    try:
        item_data = r.json()['Items'][0]["Item"]
        title = item_data.get('title')
        author = item_data.get('author')
        image = item_data.get('largeImageUrl')
        return(title, author, image)

    except IndexError:
        error = "本の情報を取得するのに失敗しました。終了します。"
        return error

# 　登録されている本から修正する本を見つける
def SearchBook(book_title):
    search_books = Book.objects.filter(title__contains=book_title)
    search_books = serializers.serialize("json", search_books)
    req = json.loads(search_books)
    if req == []:
        title = ""
        return title

    else:
        fields = req[0]['fields']
        pk = req[0]['pk']
        title = fields.get('title')
        author = fields.get('author')
        image = fields.get('image')
        return(pk, title, author, image)

# 　入力した内容に対して適した本が返ってきているか
def ConfirmBook(list):
        title = list[0]
        author = list[1]
        image = list[2]

        fulfillmentMessages = {"fulfillmentMessages": [
            {
                "payload":
                {
                    "line": {
                        "type": "template",
                        "altText": "test_template",
                        "template": {
                            "type": "buttons",
                            'title': author,
                            "text": "この本ですか？",
                            "thumbnailImageUrl" : image,
                            'imageAspectRatio': "square",
                            "imageSize": "contain",
                            "actions": [
                                {
                                    "type": "message",
                                    "label": "YES",
                                    "text": "YES"
                                },
                                {
                                    "type": "message",
                                    "label": "NO",
                                    "text": "NO"
                                },
                            ]
                        }
                    }
                }
            }
        ]
        }
        return fulfillmentMessages


def Start():
    fulfillmentMessages = {"fulfillmentMessages": [
            {
              "card": {
                    "title": "読書管理",
                    "subtitle": "自分",
                    "imageUri": 'https://cdn.pixabay.com/photo/2016/06/01/06/26/open-book-1428428__340.jpg',
                    "buttons": [
                        {
                            "text": "本棚に追加",
                        },
                        {
                            "text": "フレーズの登録",
                        },
                        {
                            "text": "本棚から削除",
                        },
                        {
                            "text": "キャンセル",
                        }
                    ]
                }
            }
        ]
        }
    return fulfillmentMessages


def CheckBook(list):
    title = list[0]
    # , author__iexact=author
    book_exact = Book.objects.filter(title__iexact=title)
    if book_exact.first() is None:
        msg = ""
        return msg

    else:
        msg = 'すでに登録されています'
        return msg
