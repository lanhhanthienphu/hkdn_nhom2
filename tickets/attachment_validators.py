"""Validate attachment bytes without saving them or depending on Ticket models."""

from io import BytesIO
from pathlib import Path
import re
import warnings

from django.core.exceptions import ValidationError
from PIL import Image
from pypdf import PdfReader


MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ATTACHMENT_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.txt', '.log'}
MAX_ATTACHMENT_IMAGE_PIXELS = 20_000_000
IMAGE_FORMATS = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG'}
TEXT_CONTROL_CHARACTERS = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')


def _validate_image(data, extension):
    expected_format = IMAGE_FORMATS[extension]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data), formats=['JPEG', 'PNG']) as image:
                if image.format != expected_format:
                    raise ValidationError(
                        'Nội dung ảnh không khớp với đuôi file. Hãy xuất lại ảnh đúng định dạng.',
                        code='attachment_image_format',
                    )
                if image.width * image.height > MAX_ATTACHMENT_IMAGE_PIXELS:
                    raise ValidationError(
                        'Ảnh vượt quá 20 triệu điểm ảnh. Vui lòng giảm kích thước ảnh.',
                        code='attachment_image_pixels',
                    )
                image.verify()
            # Reopen after verify; load also detects incomplete pixel data.
            with Image.open(BytesIO(data), formats=[expected_format]) as image:
                image.load()
    except ValidationError:
        raise
    except Exception as exc:
        # Malformed input can trigger different exceptions in image decoders.
        raise ValidationError(
            'File ảnh bị lỗi hoặc không phải ảnh JPG/PNG hợp lệ.',
            code='attachment_image',
        ) from exc


def _validate_pdf(data):
    reader = None
    try:
        if not data.startswith(b'%PDF-'):
            raise ValidationError('File không phải PDF hợp lệ.', code='attachment_pdf')
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ValidationError(
                'Chưa hỗ trợ PDF có mật khẩu hoặc mã hóa. Vui lòng chọn bản không khóa.',
                code='attachment_pdf_encrypted',
            )
        if len(reader.pages) == 0:
            raise ValidationError('PDF cần có ít nhất một trang.', code='attachment_pdf_empty')
    except ValidationError:
        raise
    except Exception as exc:
        # Keep parser failures attached to the form field instead of returning 500.
        raise ValidationError(
            'File PDF bị lỗi hoặc có cấu trúc không được hỗ trợ. Hãy xuất lại file.',
            code='attachment_pdf',
        ) from exc
    finally:
        if reader is not None:
            reader.close()


def _validate_text(data):
    encoding = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    try:
        text = data.decode(encoding)
    except UnicodeError as exc:
        raise ValidationError(
            'File TXT/LOG cần dùng UTF-8 hoặc UTF-16 có BOM. Hãy lưu lại file với mã hóa này.',
            code='attachment_text',
        ) from exc
    if not text or TEXT_CONTROL_CHARACTERS.search(text):
        raise ValidationError(
            'File TXT/LOG rỗng hoặc chứa dữ liệu nhị phân không hợp lệ.',
            code='attachment_text',
        )


def validate_attachment(attachment):
    """Raise ValidationError for invalid uploads; preserve the stream position.

    content_type is deliberately ignored because it is provided by the client.
    This checks file formats, not malware. Download permission belongs to the
    future Ticket integration, where files should be returned as attachments.
    """
    extension = Path(attachment.name).suffix.lower()
    if extension not in ATTACHMENT_EXTENSIONS:
        raise ValidationError(
            'Chỉ chấp nhận file JPG, JPEG, PNG, PDF, TXT hoặc LOG.',
            code='attachment_extension',
        )
    if attachment.size > MAX_ATTACHMENT_BYTES:
        raise ValidationError('File vượt quá 10 MB.', code='attachment_too_large')
    if attachment.size <= 0:
        raise ValidationError('Không chấp nhận file rỗng.', code='attachment_empty')

    position = attachment.tell()
    try:
        attachment.seek(0)
        # Read a bounded number of bytes, including when size metadata is wrong.
        data = attachment.read(MAX_ATTACHMENT_BYTES + 1)
        if len(data) > MAX_ATTACHMENT_BYTES:
            raise ValidationError('File vượt quá 10 MB.', code='attachment_too_large')
        if not data:
            raise ValidationError('Không chấp nhận file rỗng.', code='attachment_empty')
        if extension in IMAGE_FORMATS:
            _validate_image(data, extension)
        elif extension == '.pdf':
            _validate_pdf(data)
        else:
            _validate_text(data)
    finally:
        # Later storage must still receive the complete, open upload stream.
        attachment.seek(position)
