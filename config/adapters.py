from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages

class DomeSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        email = sociallogin.user.email
        if not email or not email.lower().endswith('@dome.tu.ac.th'):
            messages.error(request, "การเข้าสู่ระบบล้มเหลว: อนุญาตเฉพาะบัญชีอีเมล @dome.tu.ac.th เท่านั้น")
            raise ImmediateHttpResponse(HttpResponseRedirect(reverse('account_login')))
