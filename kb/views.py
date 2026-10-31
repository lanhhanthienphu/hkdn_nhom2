from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Article


def article_list(request):
    query = request.GET.get("q", "").strip()

    articles = Article.objects.filter(is_published=True)

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
        )

    return render(
        request,
        "kb/article_list.html",
        {
            "articles": articles,
            "query": query,
        },
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