from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.models import AgentProfile, AgentRequest


class ConsentMixin:
    def validate_personal_data_consent(self, value):
        if not value:
            raise serializers.ValidationError('Требуется согласие на обработку персональных данных.')
        return value


class AgentRequestCreateSerializer(ConsentMixin, serializers.ModelSerializer):
    """Заявка только с формы; учётная запись создаётся администратором вручную."""

    personal_data_consent = serializers.BooleanField()

    class Meta:
        model = AgentRequest
        fields = ('name', 'phone', 'personal_data_consent')


class AgentTokenObtainSerializer(TokenObtainPairSerializer):
    personal_data_consent = serializers.BooleanField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].help_text = 'Логин (username)'

    def validate(self, attrs):
        consent = attrs.pop('personal_data_consent', False)
        if not consent:
            raise serializers.ValidationError(
                {'personal_data_consent': 'Требуется согласие на обработку персональных данных.'}
            )
        data = super().validate(attrs)
        if not self.user.is_verified:
            raise serializers.ValidationError(
                {'detail': 'Учётная запись ещё не подтверждена администратором. Вход невозможен.'}
            )
        data['username'] = self.user.username
        data['is_verified'] = self.user.is_verified
        return data


class AgentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    is_verified = serializers.BooleanField(source='user.is_verified', read_only=True)

    class Meta:
        model = AgentProfile
        fields = (
            'id',
            'username',
            'email',
            'is_verified',
            'full_name',
            'phone',
            'description',
        )


class AgentProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False)

    class Meta:
        model = AgentProfile
        fields = ('full_name', 'phone', 'description', 'email')

    def update(self, instance, validated_data):
        email = validated_data.pop('email', None)
        if email is not None:
            instance.user.email = email
            instance.user.save(update_fields=['email'])
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Пароли не совпадают.'})
        validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user
