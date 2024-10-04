import os
from io import BytesIO

from django.core.exceptions import ValidationError
from django.db import models
from PIL import Image
import pillow_avif

class ImageField(models.ImageField):
    """
        A subclass of Django's ImageField that convert the image to a webp format
    """

    def __init__(self, *args, **kwargs):
        self.convert_to_webp = kwargs.pop("convert_to_webp", True)
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        file = super().pre_save(model_instance, add)
        if not file:
            return file
        if self.convert_to_webp:
            try:
                img = Image.open(file)
                if img.format not in ["WEBP", "AVIF"]:
                    buffer = BytesIO()
                    img.save(buffer, format="WEBP")
                    buffer.seek(0)
                    file.save(
                        os.path.basename(os.path.splitext(file.name)[0]) + ".webp",
                        buffer,
                        save=False,
                    )
            except Exception as e:
                raise ValidationError(f"Invalid image file: {e}") from e
        return file
