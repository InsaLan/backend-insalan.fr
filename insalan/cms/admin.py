"""
This module contains the admin configuration for the CMS app.

It defines the admin classes for the Constant and Content models, and registers them with the Django
admin site.
"""
from typing import Any

from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _
from django.db.models import OuterRef, Count, Subquery, QuerySet
from django.forms.models import ModelForm
from django.http import HttpRequest
from django.utils.html import format_html
from unfold.admin import ModelAdmin # type: ignore
from unfold.widgets import UnfoldAdminTextareaWidget as Textarea

from .models import Constant, Content, File, AvailableLang


class ConstantAdmin(ModelAdmin):  # type: ignore
    """
    Admin class for the Constant model
    """
    list_display = ("name", "value")
    search_fields = ["name"]

class ContentForm(ModelForm[Content]):#pylint: disable=unsubscriptable-object
    content_fr = forms.CharField(
        label = "fr",
        required = False,
        widget = Textarea(),
    )
    content_en = forms.CharField(
        label="en",
        required=False,
        widget=Textarea(),
    )
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.original_name = self.instance.name if self.instance.pk else None

        if self.instance.pk:
            translations = Content.objects.filter(name=self.original_name)
            for translation in translations:
                key = f'content_{translation.lang}'
                self.initial[key] = translation.content # type: ignore[index]
                                                        #I mean it works ? so idk if the
                                                        # complaint is valid

    def save(self, commit: bool = True) -> Content:
        instance = super().save(commit)
        form_name = self.instance.name if self.instance.pk else self.cleaned_data["name"]

        with transaction.atomic():
            for lang in AvailableLang.values:
                translation = Content.objects.filter(
                                name=form_name,
                                lang=lang).first() or Content(name=form_name, lang=lang)
                translation.name = self.cleaned_data["name"]
                translation.lang = lang
                translation.content = self.cleaned_data[f"content_{lang}"]
                translation.full_clean()
                translation.save()
        instance.name = self.cleaned_data["name"]
        instance.content = self.cleaned_data[f"content_{instance.lang}"]
        return instance

    class Meta:
        model = Content
        fields = ["name", *(f"content_{lang}" for lang in AvailableLang.values)]
        fields_classes = {
            **{f"content_{lang}": forms.CharField for lang in AvailableLang.values},
        }
        widgets = {
            **{f"content_{lang}": Textarea() for lang in AvailableLang.values},
        }

class ContentAdmin(ModelAdmin): #type: ignore
    """
    Admin class for the Content model
    """
    form = ContentForm
    list_display = ("name", "translation_status")
    search_fields = ["name"]
    def get_queryset(self, request: HttpRequest) -> QuerySet[Content]:
        translation_count = (
            Content.objects
            .filter(name=OuterRef("name"))
            .values("name")
            .annotate(count=Count("pk"))
            .values("count")
        )

        first_content = (
            Content.objects
            .filter(name=OuterRef("name"))
            .order_by("pk")
            .values("pk")[:1]
        )
        return (# type: ignore[no-any-return]
            super()#tf ? it isn't any ? get_queryset return the same type as me, and all the other
            .get_queryset(request)#return the current instance, so the end result should be of the
            .annotate(translation_count=Subquery(translation_count))#expected type...
            .filter(pk=Subquery(first_content))
            .order_by("name")
        )



    @admin.display(description="Translations", ordering="translation_count")
    def translation_status(self, obj: Content) -> SafeString:
        expected = len(AvailableLang.values)
        actual = obj.translation_count # type: ignore[attr-defined]
                                       # is dynamically added by annotation
        if expected == actual:
            return format_html(
                '<span style="color: #15803d; font-weight: 600;">'
                f"{_('Complète')}" + " ({}/{})"
                "</span>",
                actual,
                expected,
            )

        return format_html(
            '<span style="color: #dc2626; font-weight: 600;">'
            f"{_('Incomplète')}" + " ({}/{})"
                                   "</span>",
            actual,
            expected,
            )

admin.site.register(Constant, ConstantAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(File)
