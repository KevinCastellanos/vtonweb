from django import forms
from django.conf import settings

from .models import TryOnJob


class TryOnForm(forms.Form):
    person = forms.ImageField(label="Foto de la persona")
    garment = forms.ImageField(label="Foto de la prenda")
    category = forms.ChoiceField(choices=TryOnJob.CATEGORIES, label="Tipo de prenda")
    garment_photo_type = forms.ChoiceField(choices=TryOnJob.PHOTO_TYPES, label="Foto de la prenda")

    def _check_size(self, name):
        f = self.cleaned_data[name]
        if f.size > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise forms.ValidationError(f"Máximo {settings.MAX_UPLOAD_MB} MB por imagen.")
        return f

    def clean_person(self):
        return self._check_size("person")

    def clean_garment(self):
        return self._check_size("garment")
