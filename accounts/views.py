from django.shortcuts import render, redirect
from django.views import View
from .forms import UserRegistrationForm, UserLoginForm, VerifyCodeForm
import random, pytz
from datetime import datetime, timedelta
from utils import send_otp_code
from .models import OtpCode, User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout


class UserRegisterView(View):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            random_code = random.randint(1000, 9999)
            send_otp_code(form.cleaned_data['phone'], random_code)
            OtpCode.objects.create(phone_number=form.cleaned_data['phone'], code=random_code)
            request.session['user_registration_info'] = {
                'phone_number': form.cleaned_data['phone'],
                'email': form.cleaned_data['email'],
                'full_name': form.cleaned_data['full_name'],
                'password': form.cleaned_data['password'],
            }
            messages.success(request, 'we sent you an email', 'success')
            return redirect('accounts:verify_code')
        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    form_class = UserLoginForm
    template_name = 'accounts/login.html'

    def get(self, request):
        form = self.form_class
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(request, email=cd['phone'], password=cd['password'])
            if user is not None:
                login(request, user)
                random_code = random.randint(1000, 9999)
                send_otp_code(form.cleaned_data['phone'], random_code)
                OtpCode.objects.create(phone_number=form.cleaned_data['phone'], code=random_code)
                request.session['user_registration_info'] = {
                    'phone_number': form.cleaned_data['phone'],
                    'password': form.cleaned_data['password'],
                }
                messages.success(request, 'we sent you an email', 'success')
                return redirect('accounts:verify_code')
            messages.error(request, 'username or password is wrong', 'warning')
        return render(request, self.template_name, {'form': form})


class UserVerifyCodeView(View):
    form_class = VerifyCodeForm

    def get(self, request):
        form = self.form_class
        return render(request, 'accounts/verify.html', {'form': form})

    def post(self, request):
        user_session = request.session['user_registration_info']
        code_instance = OtpCode.objects.get(phone_number=user_session['phone_number'])
        form = self.form_class(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # adding two-step verification

            diff = False

            created_data = code_instance.created
            expiry = created_data + timedelta(seconds=30)
            now = datetime.now().replace(tzinfo=pytz.utc)
            if expiry.replace(tzinfo=pytz.utc) < now:
                diff = True
            if cd['code'] == code_instance.code and diff:
                User.objects.create_user(phone_number=user_session['phone_number'], email=user_session['email'],
                                         full_name=user_session['full_name'], password=user_session['password'])
                code_instance.delete()
                messages.success(request, 'you registered :)', 'success')
                return redirect('home:home')
            else:
                messages.error(request, 'Invalid Code :/', 'danger')
                return redirect('accounts:verify_code')
        return redirect('home:home')
