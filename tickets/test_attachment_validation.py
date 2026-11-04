from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import SimpleTestCase
from PIL import Image
from pypdf import PdfWriter

from .attachment_validators import MAX_ATTACHMENT_BYTES, validate_attachment
from .forms import TicketForm


def image_bytes(format_name='PNG'):
    output = BytesIO()
    with Image.new('RGB', (4, 4), color='white') as image:
        image.save(output, format=format_name)
    return output.getvalue()


def pdf_bytes(*, encrypted=False, with_page=True):
    output = BytesIO()
    writer = PdfWriter()
    if with_page:
        writer.add_blank_page(width=100, height=100)
    if encrypted:
        writer.encrypt('test-password', algorithm='RC4-128')
    writer.write(output)
    writer.close()
    return output.getvalue()


class AttachmentValidatorTests(SimpleTestCase):
    def assert_invalid(self, upload, code):
        with self.assertRaises(ValidationError) as caught:
            validate_attachment(upload)
        self.assertEqual(caught.exception.code, code)

    def test_valid_images_and_uppercase_extensions(self):
        for name, format_name in [('screen.PNG', 'PNG'), ('screen.jpg', 'JPEG'), ('screen.jpeg', 'JPEG')]:
            with self.subTest(name=name):
                validate_attachment(SimpleUploadedFile(name, image_bytes(format_name)))

    def test_fake_image_is_rejected(self):
        upload = SimpleUploadedFile('screen.png', b'not an image', content_type='image/png')
        self.assert_invalid(upload, 'attachment_image')

    def test_image_extension_must_match_content(self):
        self.assert_invalid(
            SimpleUploadedFile('screen.jpg', image_bytes('PNG')),
            'attachment_image_format',
        )

    def test_truncated_images_are_rejected(self):
        for name, data in [('screen.png', image_bytes()[:-12]), ('screen.jpg', image_bytes('JPEG')[:-30])]:
            with self.subTest(name=name):
                self.assert_invalid(SimpleUploadedFile(name, data), 'attachment_image')

    def test_image_pixel_limit(self):
        with patch('tickets.attachment_validators.MAX_ATTACHMENT_IMAGE_PIXELS', 10):
            self.assert_invalid(
                SimpleUploadedFile('screen.png', image_bytes()),
                'attachment_image_pixels',
            )

    def test_valid_pdf(self):
        validate_attachment(SimpleUploadedFile('report.pdf', pdf_bytes()))

    def test_fake_pdf_is_rejected(self):
        self.assert_invalid(SimpleUploadedFile('report.pdf', b'not a pdf'), 'attachment_pdf')

    def test_pdf_signature_alone_is_not_enough(self):
        self.assert_invalid(
            SimpleUploadedFile('report.pdf', b'%PDF-1.7\nnot a document\n%%EOF'),
            'attachment_pdf',
        )

    def test_encrypted_pdf_is_rejected(self):
        self.assert_invalid(
            SimpleUploadedFile('report.pdf', pdf_bytes(encrypted=True)),
            'attachment_pdf_encrypted',
        )

    def test_pdf_without_pages_is_rejected(self):
        self.assert_invalid(
            SimpleUploadedFile('report.pdf', pdf_bytes(with_page=False)),
            'attachment_pdf_empty',
        )

    def test_text_encodings(self):
        content = 'Lỗi kết nối mạng\r\nThiết bị: máy tính\tPhòng A.201'
        for name in ('report.txt', 'report.log'):
            for encoding in ('utf-8', 'utf-8-sig', 'utf-16'):
                with self.subTest(name=name, encoding=encoding):
                    validate_attachment(SimpleUploadedFile(name, content.encode(encoding)))

    def test_binary_text_is_rejected(self):
        self.assert_invalid(SimpleUploadedFile('report.log', b'MZ\x00\x01binary'), 'attachment_text')

    def test_invalid_text_encoding_is_rejected(self):
        self.assert_invalid(SimpleUploadedFile('report.txt', b'\xff\x80bad'), 'attachment_text')

    def test_unsupported_extensions_are_rejected(self):
        for name in ('payload.exe', 'screen.svg', 'report.html', 'no-extension'):
            with self.subTest(name=name):
                self.assert_invalid(SimpleUploadedFile(name, b'data'), 'attachment_extension')

    def test_empty_files_are_rejected(self):
        self.assert_invalid(SimpleUploadedFile('report.txt', b''), 'attachment_empty')

    def test_exactly_ten_mebibytes_is_accepted(self):
        validate_attachment(SimpleUploadedFile('report.log', b'a' * MAX_ATTACHMENT_BYTES))

    def test_more_than_ten_mebibytes_is_rejected(self):
        self.assert_invalid(
            SimpleUploadedFile('report.log', b'a' * (MAX_ATTACHMENT_BYTES + 1)),
            'attachment_too_large',
        )

    def test_actual_bytes_are_checked_when_size_metadata_is_wrong(self):
        upload = SimpleUploadedFile('report.log', b'a' * (MAX_ATTACHMENT_BYTES + 1))
        upload.size = 1
        self.assert_invalid(upload, 'attachment_too_large')

    def test_client_mime_type_is_not_trusted(self):
        validate_attachment(SimpleUploadedFile('screen.png', image_bytes(), content_type='application/octet-stream'))
        self.assert_invalid(
            SimpleUploadedFile('screen.png', b'fake', content_type='image/png'),
            'attachment_image',
        )

    def test_stream_is_preserved_after_success_and_failure(self):
        for name, data, valid in [('report.log', b'network error', True), ('screen.png', b'fake image', False)]:
            with self.subTest(name=name):
                upload = SimpleUploadedFile(name, data)
                upload.seek(2)
                if valid:
                    validate_attachment(upload)
                else:
                    self.assert_invalid(upload, 'attachment_image')
                self.assertEqual(upload.tell(), 2)
                self.assertFalse(upload.closed)
                upload.seek(0)
                self.assertEqual(upload.read(), data)

    def test_disk_backed_upload(self):
        data = 'Nhật ký lỗi mạng'.encode('utf-8')
        with TemporaryUploadedFile('report.log', 'text/plain', len(data), None) as upload:
            upload.write(data)
            upload.seek(0)
            validate_attachment(upload)
            self.assertEqual(upload.read(), data)


class TicketAttachmentFormTests(SimpleTestCase):
    def form_data(self):
        return {
            'title': 'Khong ket noi duoc Wi-Fi',
            'description': 'May tinh khong ket noi duoc mang Wi-Fi trong phong hoc.',
            'location': 'A.201',
            'category': 'network',
            'priority': 'normal',
        }

    def test_attachment_remains_optional(self):
        form = TicketForm(data=self.form_data())
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertIsNone(form.cleaned_data['attachment'])

    def test_valid_attachment_survives_form_cleaning(self):
        cases = [
            ('screen.png', image_bytes()),
            ('screen.jpg', image_bytes('JPEG')),
            ('report.pdf', pdf_bytes()),
            ('report.txt', b'network error'),
            ('report.log', b'network error'),
        ]
        for name, data in cases:
            with self.subTest(name=name):
                upload = SimpleUploadedFile(name, data)
                form = TicketForm(data=self.form_data(), files={'attachment': upload})
                self.assertTrue(form.is_valid(), form.errors.as_json())
                self.assertIs(form.cleaned_data['attachment'], upload)
                self.assertEqual(upload.read(), data)

    def test_invalid_attachment_sets_field_error_and_keeps_text(self):
        for name, data in [('screen.png', b'fake'), ('report.exe', b'fake'), ('report.log', b'a' * (MAX_ATTACHMENT_BYTES + 1))]:
            with self.subTest(name=name):
                form = TicketForm(
                    data=self.form_data(),
                    files={'attachment': SimpleUploadedFile(name, data)},
                )
                self.assertFalse(form.is_valid())
                self.assertEqual(set(form.errors), {'attachment'})
                self.assertEqual(form['title'].value(), self.form_data()['title'])
                self.assertEqual(form['description'].value(), self.form_data()['description'])
