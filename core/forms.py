from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class ClientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")


class EmailOrUsernameAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(attrs={"autofocus": True}),
    )

    def clean_username(self):
        identifier = self.cleaned_data["username"].strip()
        user_model = get_user_model()
        if "@" in identifier:
            matched_user = user_model.objects.filter(email__iexact=identifier).first()
            if matched_user:
                return matched_user.get_username()
        return identifier
