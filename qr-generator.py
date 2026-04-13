import qrcode
import io
from PyQt5.QtGui import QPixmap


class QRGenerator:
    SURVEY_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform?usp=sf_link"

    @classmethod
    def generate_qr_code(cls, request_id: int = None) -> QPixmap:
        url = cls.SURVEY_URL
        if request_id:
            url += f"&entry.request_id={request_id}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        return pixmap