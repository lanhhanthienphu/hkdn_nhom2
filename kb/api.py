from functools import wraps
from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.cache import never_cache

from .models import Article


PAGE_SIZE = 6


def json_response(data, status=200):
    return JsonResponse(
        data,
        status=status,
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


def api_read_only(view):
    """Require a session login and allow only GET/HEAD."""
    @wraps(view)
    @never_cache
    def wrapped(request, *args, **kwargs):
        # Keep the endpoint protected even if global middleware is changed.
        if not request.user.is_authenticated:
            return json_response({
                "error": "authentication_required",
                "message": "Vui lòng đăng nhập để xem kho kiến thức.",
            }, status=401)

        if request.method not in ("GET", "HEAD"):
            response = json_response({
                "error": "method_not_allowed",
                "message": "API này chỉ hỗ trợ GET và HEAD.",
            }, status=405)
            response["Allow"] = "GET, HEAD"
            return response

        return view(request, *args, **kwargs)

    return wrapped


def article_data(article):
    # Expose only the fields needed by the article reader.
    return {
        "id": article.pk,
        "title": article.title,
        "content": article.content,
        "created_at": article.created_at,
        "updated_at": article.updated_at,
    }


@api_read_only
def article_list(request):
    query = request.GET.get("q", "").strip()
    articles = Article.objects.filter(is_published=True).order_by(
        "-created_at", "-pk"
    )

    if query:
        articles = articles.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    paginator = Paginator(articles, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    def page_link(number):
        return request.path + "?" + urlencode({"q": query, "page": number})

    return json_response({
        "query": query,
        "count": paginator.count,
        "page": page.number,
        "page_size": PAGE_SIZE,
        "num_pages": paginator.num_pages,
        "next": page_link(page.next_page_number()) if page.has_next() else None,
        "previous": (
            page_link(page.previous_page_number()) if page.has_previous() else None
        ),
        "results": [article_data(article) for article in page],
    })


@api_read_only
def article_detail(request, pk):
    article = Article.objects.filter(pk=pk, is_published=True).first()
    if article is None:
        return json_response({
            "error": "not_found",
            "message": "Không tìm thấy bài hướng dẫn.",
        }, status=404)

    return json_response(article_data(article))
