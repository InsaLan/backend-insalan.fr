"""
This module contains the admin configuration for the CMS app.

It defines the admin classes for the Constant and Content models, and registers them with the Django
admin site.
"""
from logging import getLogger
from typing import Any, TypeVar, Generic, Type, Callable

from django import forms
from django.contrib import admin
from django.db import transaction
from django.utils.safestring import SafeString
from django.utils.translation import gettext as _
from django.db.models import OuterRef, Count, Subquery, QuerySet, Model
from django.forms.models import ModelForm
from django.http import HttpRequest
from django.utils.html import format_html
from unfold.admin import ModelAdmin # type: ignore
from unfold.widgets import UnfoldAdminTextareaWidget as Textarea #type: ignore

from .models import Constant, Content, File, AvailableLang, CommonFieldInterface

T = TypeVar("T", bound=CommonFieldInterface)


class TranslatedForm(ModelForm[T], Generic[T]):#pylint: disable=unsubscriptable-object
    t: Type[T]
    get_value: Callable[[T], str]
    set_value: Callable[[T, str], None]
    field_fr = forms.CharField(
        label = "fr",
        required = False,
        widget = Textarea(),
    )
    field_en = forms.CharField(
        label="en",
        required=False,
        widget=Textarea(),
    )
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.original_name = self.instance.name if self.instance.pk else None

        if self.instance.pk:
            translations = self.t.objects.filter(name=self.original_name)
            for translation in translations:
                key = f'field_{translation.lang}'
                self.initial[key] = self.get_value(translation) # type: ignore[index, union-attr]
                                                        #I mean it works ? so idk if the
                                                        # complaint is valid

    def save(self, commit: bool = True) -> T:
        instance = super().save(commit)
        form_name = self.instance.name if self.instance.pk else self.cleaned_data["name"]

        with transaction.atomic():
            for lang in AvailableLang.values:
                translation = self.t.objects.filter(
                                name=form_name,
                                lang=lang).first() or Content(name=form_name, lang=lang)
                translation.name = self.cleaned_data["name"]
                translation.lang = lang
                self.set_value(translation, self.cleaned_data[f"field_{lang}"])
                translation.full_clean()
                translation.save()
        instance.name = self.cleaned_data["name"]
        self.set_value(translation, self.cleaned_data[f"field_{instance.lang}"])
        return instance

    class Meta:
        fields = ["name", *(f"field_{lang}" for lang in AvailableLang.values)]
        fields_classes = {
            **{f"field_{lang}": forms.CharField for lang in AvailableLang.values},
        }
        widgets = {
            **{f"field_{lang}": Textarea() for lang in AvailableLang.values},
        }


class ContentForm(TranslatedForm[Content]):
    t = Content
    get_value = lambda obj: obj.content
    set_value = lambda obj, value: setattr(obj, "content", value)

    class Meta(TranslatedForm.Meta):
        model = Content

class ConstantForm(TranslatedForm[Constant]):
    t = Constant
    get_value = lambda obj: obj.value
    set_value = lambda obj, value: setattr(obj, "value", value)

    class Meta(TranslatedForm.Meta):
        model = Constant

M = TypeVar("M", bound=CommonFieldInterface)

class TranslatableAdmin(ModelAdmin, Generic[M]): #type: ignore
    """
    Abstract class for constant & content
    """
    t: type[M]
    form: type[TranslatedForm[M]]
    list_display = ("name", "translation_status")
    search_fields = ["name"]
    def get_queryset(self, request: HttpRequest) -> QuerySet[M]:
        translation_count = (
            self.t.objects
            .filter(name=OuterRef("name"))
            .values("name")
            .annotate(count=Count("pk"))
            .values("count")
        )

        first_content = (
            self.t.objects
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
    def translation_status(self, obj: M) -> SafeString:
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

class ConstantAdmin(TranslatableAdmin[Constant]):  # type: ignore
    """
    Admin class for the Constant model
    """
    t = Constant
    form = ConstantForm

class ContentAdmin(TranslatableAdmin[Content]):
    """
    Admin class for the Content model
    """
    t = Content
    form = ContentForm

admin.site.register(Constant, ConstantAdmin)
admin.site.register(Content, ContentAdmin)
admin.site.register(File)
