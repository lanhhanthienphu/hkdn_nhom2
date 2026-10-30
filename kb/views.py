from django.shortcuts import get_object_or_404, render
from .models import Article


def article_list(request):
    articles = Article.objects.filter(is_published=True)

    return render(
        request,
        "kb/article_list.html",
        {"articles": articles},
    )


def article_detail(request, pk):
    article = get_object_or_404(
        Article,
        pk=pk,
        is_published=True,
    )

    return render(
        request,
        "kb/article_detail.html",
        {"article": article},
    )