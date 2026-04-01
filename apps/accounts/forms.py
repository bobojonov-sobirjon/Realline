from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import AgentProfile

User = get_user_model()


class AgentProfileInlineForm(forms.ModelForm):
    """Поля профиля + подтверждение пользователя (хранится в CustomUser)."""

    user_is_verified = forms.BooleanField(
        required=False,
        label='Подтверждён администратором',
        help_text=(
            'Для входа в API должен быть включён. При создании кабинета из заявки выставляется автоматически; '
            'вручную — для пользователей, заведённых только через админку.'
        ),
    )

    class Meta:
        model = AgentProfile
        fields = ('full_name', 'phone', 'description')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'user_id', None):
            self.fields['user_is_verified'].initial = self.instance.user.is_verified

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if commit and profile.user_id is not None:
            uv = self.cleaned_data.get('user_is_verified')
            User.objects.filter(pk=profile.user_id).update(is_verified=bool(uv))
        return profile


class CreateAgentCabinetForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Пароль ещё раз', widget=forms.PasswordInput)
    email = forms.EmailField(
        label='Email',
        required=False,
        help_text='Необязательно. Если пусто — будет сгенерирован служебный email.',
    )

    def clean_username(self):
        u = self.cleaned_data['username'].strip()
        if User.objects.filter(username=u).exists():
            raise forms.ValidationError('Пользователь с таким логином уже есть.')
        return u

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('Этот email уже занят.')
        return email

    def clean(self):
        data = super().clean()
        p1, p2 = data.get('password1'), data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Пароли не совпадают.')
        if p1:
            validate_password(p1)
        return data
