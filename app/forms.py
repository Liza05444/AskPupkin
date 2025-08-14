from django.contrib.auth import login as auth_login, update_session_auth_hash, authenticate
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError

from .models import Question, Answer, Tag, Profile


class LoginForm(forms.Form):
    username = forms.CharField(max_length=20)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')
        self.user = authenticate(username=username, password=password)
        if not self.user:
            raise forms.ValidationError("Invalid login or password")
        return cleaned_data

    def get_user(self):
        return self.user


class SignUpForm(forms.Form):
    username = forms.CharField(max_length=20)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm password")
    avatar = forms.ImageField(required=False)

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already registered")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise ValidationError("Passwords should match")
        return cleaned_data

    def save(self, request=None):
        user = User.objects.create_user(username=self.cleaned_data['username'], email=self.cleaned_data['email'],
                                        password=self.cleaned_data['password'])
        profile = Profile.objects.create(user=user, avatar=self.cleaned_data.get('avatar'))
        if request:
            auth_login(request, user)
        return user


class ProfileSettingsForm(forms.ModelForm):
    username = forms.CharField(max_length=20)
    email = forms.EmailField()
    old_password = forms.CharField(widget=forms.PasswordInput, required=False, label='Current password')
    new_password1 = forms.CharField(widget=forms.PasswordInput, required=False, label='New password')
    new_password2 = forms.CharField(widget=forms.PasswordInput, required=False, label='Confirm new password')

    class Meta:
        model = Profile
        fields = ['avatar']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].initial = self.instance.user.username
        self.fields['email'].initial = self.instance.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.user.pk).filter(username=username).exists():
            raise ValidationError("This username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.exclude(pk=self.instance.user.pk).filter(email=email).exists():
            raise ValidationError("Email already registered")
        return email

    def clean(self):
        cleaned_data = super().clean()
        old_password = self.cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 or new_password2:
            if len(new_password1) < 4:
                self.add_error('new_password1', "Too short password")
            if new_password1 != new_password2:
                self.add_error('new_password2', "New passwords should match")
            if not self.instance.user.check_password(old_password):
                self.add_error('old_password', "Please enter valid current password to change password")
        return cleaned_data

    def save(self, request=None, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.save()
        if self.cleaned_data['avatar']:
            profile.avatar = self.cleaned_data['avatar']
        profile.save()
        new_password = self.cleaned_data.get('new_password1')
        old_password = self.cleaned_data.get('old_password')
        if new_password and user.check_password(old_password):
            user.set_password(new_password)
            user.save()
            if request:
                update_session_auth_hash(request, user)
        return profile


class AskQuestionForm(forms.ModelForm):
    tags = forms.CharField(required=True, help_text="Enter tags separated by commas",
                           widget=forms.TextInput(attrs={'placeholder': 'django, python, web'}))

    class Meta:
        model = Question
        fields = ['title', 'text']

    def clean_tags(self):
        tags_str = self.cleaned_data.get('tags')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        if len(tags) > 3:
            raise forms.ValidationError("You can't add more than 3 tags.")
        return tags

    def save(self, author=None, commit=True):
        question = super().save(commit=False)
        question.author = author
        question.save()
        tags = self.cleaned_data['tags']
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
            question.tags.add(tag)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        widgets = {'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your answer here...'})}

    def save(self, author=None, question=None, commit=True):
        answer = super().save(commit=False)
        answer.author = author
        answer.question = question
        answer.save()
        return answer
