from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Article


def article_list(request):
    query = request.GET.get("q", "").strip()

    articles = Article.objects.filter(
        is_published=True
    ).order_by("-created_at", "-pk")

    if query:
        articles = articles.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
        )

    paginator = Paginator(articles, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "kb/article_list.html",
        {
            "articles": page_obj,
            "page_obj": page_obj,
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