from user.models import Profile
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView,PasswordResetView,PasswordResetConfirmView
from django.contrib.auth.forms import PasswordResetForm,SetPasswordForm
from django.urls import reverse_lazy
from .forms import FileFieldForm,PasswordsChangingForm
from django.views.generic.edit import FormView
from .models import MyModel
from datetime import datetime
import os
import shutil
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
# gauth = GoogleAuth()
# gauth.LocalWebserverAuth()
# drive = GoogleDrive(gauth)
class PasswordsChangeView(PasswordChangeView):
    form_class = PasswordsChangingForm
    success_url = reverse_lazy('password_change_done')

def PasswordChangeDoneView(request):
    return render(request,'password_change_done.html')

class PasswordsResetView(PasswordResetView):
    form_class = PasswordResetForm
    success_url = reverse_lazy('password_reset_done')

def PasswordResetDoneView(request):
    return render(request,'password_reset_done.html')
class PasswordsResetConfirmView(PasswordResetConfirmView):
    form_class = SetPasswordForm
    success_url = reverse_lazy('password_reset_complete')





@login_required(login_url="login_attempt")
def home(request):
    return render(request, 'home.html')


def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request, 'Tên người dùng không tồn tại')
            return redirect('/accounts/login')

        profile_obj = Profile.objects.filter(user=user_obj).first()

        if not profile_obj.is_verified:
            messages.success(request, 'Tài khoản chưa xác thực vui lòng kiểm tra email')
            return redirect('/accounts/login')

        user = authenticate(username=username, password=password)
        if user is None:
            messages.success(request, 'Sai mật khẩu')
            return redirect('/accounts/login')

        login(request, user)
        return redirect('/')

    return render(request, 'dangnhap.html')


def register_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            if User.objects.filter(username=username).first():
                messages.success(request, 'Tên người dùng để trống hoặc đã tồn tại')
                return redirect('/register')

            if User.objects.filter(email=email).first():
                messages.success(request, 'Email đã tồn tại')
                return redirect('/register')

            user_obj = User(username=username, email=email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj = Profile.objects.create(user=user_obj, auth_token=auth_token)
            profile_obj.save()
            send_mail_after_registration(email, auth_token)
            return redirect('/token')
        except Exception as e:
            print(e)
    return render(request, 'dangki.html')


def success(request):
    return render(request, 'success.html')


def token_send(request):
    return render(request, 'token_send.html')


def verify(request, auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()
        if profile_obj:
            if profile_obj.is_verified:
                messages.success(request, 'Bạn đã xác thực tài khoản này rồi')
                return redirect('/accounts/login')
            profile_obj.is_verified = True
            profile_obj.save()
            messages.success(request, 'Tài khoản của bạn đã xác thực.')
            return redirect('/accounts/login')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)
        return redirect('/')


def error_page(request):
    return render(request, 'error.html')

def Dangxuat(request):
    logout(request)
    messages.success(request,'Đăng xuất thành công')
    return redirect('/accounts/login')


def send_mail_after_registration(email, auth_token):
    subject = 'Tài khoản của bạn cần xác thực'
    message = f'Nhấn vào đường link này để xác thực: http://127.0.0.1:8000/verify/{auth_token}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)

# https://accounts.google.com/DisplayUnlockCaptcha
# https://myaccount.google.com/lesssecureapps?pli=1&rapt=AEjHL4MKvsNPAkDdvjmxFXA3SG6EQk2YWe6JqfK4FVVjvrc3yuVMPlsEqpRqP2bDFwR-vAtiiUVL4sT3xFhWMCMsptJ1EZ_xJw
def myfile(request):
    nd = Profile.objects.get(user__id=request.user.id)
    context = {
    "nd":nd
    }
    return render(request, "myfile.html", context)
def uploadfile(request):
    nd = Profile.objects.get(user__id=request.user.id)
    np=myuploadfile.objects.all()
    id=request.user.id
    # urlk= os.path.join(datetime.today().year, datetime.today().month, datetime.today().day, id)
    for i in np:
        i.delete()
    if request.method == "POST":
        name = request.POST.get("filename")
        myfile = request.FILES.getlist("uploadfiles")
        urlk= str(datetime.today().year)+ str(datetime.today().month)+ str(datetime.today().day)+str(datetime.now().hour)+str(datetime.now().minute)+str(datetime.now().second)+ str(id)
        print(urlk)
        Folder='./media/'+urlk
        os.makedirs(Folder)
        for f in myfile:
            myuploadfile(f_name=name, myfiles=f,user=nd).save()
        for f in myfile:
            b=str(f)
            fr='./media/'+b
            to='./media/'+urlk
            shutil.move(fr, to)
        #     print(type(f))
        entries = os.scandir(Folder)
        f = []
        for entry in entries:
            print(entry.name)
            k = str(entry.name)
            f.append(os.path.join(Folder, k))
        folder_name = urlk
        folder = drive.CreateFile({'title': folder_name, 'mimeType': 'application/vnd.google-apps.folder'})
        folder.Upload()
        print('File ID: %s' % folder.get('id'))
        a = str(folder.get('id'))
        for upload_file in f:
            gfile = drive.CreateFile({'parents': [{'id': a}]})
            gfile.SetContentFile(upload_file)
            gfile.Upload()  # Upload the file.
            print('success')
        return redirect("/")


# def uploadfile(request):
#     if request.method == "POST":
#         myfile = request.FILES.getlist("uploadfiles")
#         for f in myfile:
#             MyModel(upload=f).save()
#         return redirect("/")
#
# class FileFieldView(FormView):
#     form_class = FileFieldForm
#     template_name = 'myfile.html'
#     # success_url = 'upload'
#
#     def post(self, request, *args, **kwargs):
#         form_class = self.get_form_class()
#         form = self.get_form(form_class)
#         files = request.FILES.getlist('file_field')
#         if form.is_valid():
#             for f in files:
#                 print("Name of file is " + f._get_name() + ' ' + f.field_name, sys.stderr)
#                 new_file = myuploadfile(file=f)
#                 new_file.save()
#             return self.form_valid(form)
#         else:
#             return self.form_invalid(form)


