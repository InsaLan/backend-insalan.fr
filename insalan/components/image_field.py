import os
from io import BytesIO
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Model
from PIL import Image
# TODO: remove pillow-avif-plugin from dependecies when updating pillow to 11.3.0
# https://github.com/python-pillow/Pillow/pull/5201#issuecomment-3023668716
import pillow_avif  # type: ignore[import]


class ImageField(models.ImageField):
    """
    A subclass of Django's ImageField that convert the image to a webp format.
    """

    def __init__(self, *args: Any, convert_to_webp: bool = True, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.convert_to_webp = convert_to_webp

    def pre_save(self, model_instance: Model, add: bool) -> Any:
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
