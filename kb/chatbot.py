"""Context-grounded helpdesk chatbot with an optional local Ollama model."""

import json
import os
import re
import unicodedata
from urllib.error import URLError
from urllib.request import Request, urlopen

from .models import Article


MAX_MESSAGE_LENGTH = 1200


def _normalize(value):
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    return re.sub(r"\bwi fi\b", "wifi", value)


def _published_articles(question, limit=4):
    terms = {term for term in _normalize(question).split() if len(term) > 2}
    scored = []
    for article in Article.objects.filter(is_published=True).only("title", "content"):
        title = _normalize(article.title)
        content = _normalize(article.content)
        score = sum(3 for term in terms if term in title)
        score += sum(1 for term in terms if term in content)
        if score:
            scored.append((score, article))
    scored.sort(key=lambda item: (-item[0], -item[1].pk))
    return [article for _, article in scored[:limit]]


def _builtin_answer(question):
    text = _normalize(question)
    if any(word in text.split() for word in ("chao", "hello", "hi", "alo")):
        return "Xin chào! Mình là trợ lý Helpdesk. Bạn có thể hỏi về cách dùng hệ thống hoặc mô tả lỗi mạng đang gặp."

    if any(term in text for term in ("cong dung", "chuc nang", "web nay", "trang web", "du an nay", "helpdesk")):
        return (
            "Đây là hệ thống Helpdesk để gửi và theo dõi yêu cầu hỗ trợ. Người dùng có thể tạo ticket, "
            "xem tiến độ và trao đổi với bộ phận kỹ thuật; kỹ thuật viên xử lý ticket, còn quản trị viên "
            "quản lý hệ thống và xem báo cáo. Bạn cũng có thể hỏi mình cách kiểm tra một số lỗi mạng cơ bản."
        )

    if any(term in text for term in ("tao ticket", "gui ticket", "bao su co", "bao loi")):
        return (
            "Để gửi yêu cầu, chọn Tạo ticket, điền tiêu đề, nhóm sự cố, vị trí và mô tả các bước đã thử; "
            "có thể đính kèm ảnh thông báo lỗi rồi gửi. Sau đó vào **Ticket của tôi** để theo dõi và phản hồi. "
            "Không ghi mật khẩu hoặc mã xác thực vào nội dung ticket."
        )

    if any(term in text for term in ("theo doi ticket", "xem ticket", "trang thai ticket")):
        return (
            "Mở mục Ticket của tôi để xem danh sách yêu cầu và trạng thái. Chọn một ticket để xem cập nhật "
            "hoặc gửi thêm thông tin cho kỹ thuật viên."
        )

    if any(term in text for term in ("mat wifi", "khong vao duoc wifi", "khong ket noi duoc wifi", "wifi khong ket noi", "khong co internet", "mat mang")):
        return (
            "Bạn thử lần lượt:\n1. Tắt chế độ máy bay và bật Wi-Fi.\n2. Kiểm tra đã chọn đúng mạng Wi-Fi; "
            "ngắt kết nối rồi kết nối lại.\n3. Thử mở một trang web khác hoặc kiểm tra thiết bị khác có vào mạng được không.\n"
            "4. Khởi động lại máy tính nếu đang không làm việc dở.\n\nNếu nhiều người cùng mất mạng hoặc vẫn không được, hãy tạo ticket và ghi tên mạng, vị trí, "
            "thời điểm, thông báo lỗi. Đừng gửi mật khẩu Wi-Fi vào ticket."
        )

    if any(term in text for term in ("mang cham", "wifi cham", "mang chap chon", "internet cham")):
        return (
            "Bạn có thể kiểm tra:\n1. Thử mở vài trang web/ứng dụng để xem lỗi xảy ra ở tất cả hay chỉ một nơi.\n"
            "2. Tạm dừng tải tệp hoặc xem video chất lượng cao.\n3. Đến gần điểm phát Wi-Fi hơn và kiểm tra lại.\n"
            "4. Hỏi người bên cạnh xem họ có gặp tình trạng tương tự không.\n\nNếu cả khu vực cùng bị chậm, hãy tạo ticket kèm vị trí và khoảng thời gian xảy ra lỗi."
        )

    if any(term in text for term in ("day mang", "cap mang", "lan", "mang day")):
        return (
            "Nếu dùng mạng dây, kiểm tra đầu cáp đã cắm chắc vào máy và ổ mạng, rồi xem đèn ở cổng mạng "
            "có sáng không. Nếu có thể, thử một sợi cáp khác đã biết là hoạt động. Đừng tự tháo hoặc cấu hình "
            "switch/router của trường. Nếu vẫn lỗi, gửi ticket kèm vị trí ổ mạng và thời điểm xảy ra."
        )

    if any(term in text for term in ("vpn", "ket noi vpn")):
        return (
            "Bạn kiểm tra Internet có hoạt động trước, ngày giờ thiết bị có chính xác và đã chọn đúng cấu hình VPN "
            "do đơn vị cấp chưa. Ghi lại mã lỗi nếu có. Không gửi mật khẩu hoặc mã xác thực; nếu vẫn không kết nối được, "
            "hãy tạo ticket để kỹ thuật viên kiểm tra."
        )

    if any(term in text for term in ("may in", "printer")):
        return (
            "Kiểm tra máy in đã bật, có giấy và không báo kẹt giấy; sau đó xác nhận bạn chọn đúng máy in của đơn vị. "
            "Nếu máy in vẫn ngoại tuyến, ghi lại tên máy in, vị trí và thông báo lỗi rồi tạo ticket."
        )

    return None


def _ollama_answer(question, history, articles):
    if os.environ.get("CHATBOT_OLLAMA_ENABLED", "0").lower() not in {"1", "true", "yes"}:
        return None

    endpoint = os.environ.get(
        "CHATBOT_OLLAMA_URL", "http://127.0.0.1:11434/api/chat"
    )
    model = os.environ.get("CHATBOT_OLLAMA_MODEL", "qwen2.5:3b")
    context = [
        "Hệ thống Helpdesk dùng để tạo/theo dõi ticket hỗ trợ, xử lý sự cố và xem báo cáo.",
        "Chỉ hướng dẫn kiểm tra mạng ở mức cơ bản: Wi-Fi, cáp, kiểm tra thiết bị khác, ghi nhận vị trí/lỗi.",
        "Không yêu cầu người dùng cung cấp mật khẩu, mã OTP; không hướng dẫn sửa router/switch hoặc thay đổi cấu hình quản trị.",
    ]
    context.extend(f"Bài hướng dẫn: {item.title}\n{item.content}" for item in articles)
    messages = [{
        "role": "system",
        "content": (
            "Bạn là trợ lý tiếng Việt của hệ thống Helpdesk. Trả lời ngắn, dễ làm theo, dùng văn bản thuần "
            "(không dùng ký hiệu Markdown), và chỉ dựa trên "
            "ngữ cảnh bên dưới cùng hướng dẫn mạng phổ thông an toàn. Nếu thiếu dữ kiện, hỏi thêm hoặc đề nghị "
            "tạo ticket; không bịa chức năng. Không yêu cầu mật khẩu/OTP, không hướng dẫn thay đổi cấu hình "
            "router/switch.\n\nNGỮ CẢNH:\n" + "\n\n".join(context)
        ),
    }]
    for item in history[-6:]:
        if item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str):
            messages.append({"role": item["role"], "content": item["content"][:MAX_MESSAGE_LENGTH]})
    messages.append({"role": "user", "content": question})

    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    request = Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        answer = data.get("message", {}).get("content", "").strip()
        return answer or None
    except (URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError):
        return None


def answer_question(question, history=None):
    question = question.strip()[:MAX_MESSAGE_LENGTH]
    articles = _published_articles(question)

    # Use the local model when configured; fall back to prepared answers if it is offline.
    answer = _ollama_answer(question, history or [], articles)
    if answer:
        return {"answer": answer, "sources": [item.title for item in articles]}

    answer = _builtin_answer(question)
    if answer:
        return {"answer": answer, "sources": []}

    if articles:
        article = articles[0]
        return {
            "answer": f"Mình tìm thấy hướng dẫn liên quan: {article.title}\n\n{article.content}",
            "sources": [item.title for item in articles],
        }

    return {
        "answer": (
            "Mình chưa tìm thấy hướng dẫn phù hợp trong nội dung hiện có. Bạn cho biết thiết bị, "
            "vị trí, thông báo lỗi và những bước đã thử nhé. Nếu sự cố vẫn tiếp diễn, hãy tạo ticket "
            "để bộ phận kỹ thuật hỗ trợ. Đừng gửi mật khẩu hoặc mã xác thực."
        ),
        "sources": [],
    }
