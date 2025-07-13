from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout
from django import forms
from .models import News, Report, MissingPerson, WantedPerson, Tip, MissingGoods, Notification
from django.db.models import Q
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime
import json
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

class WantedPersonForm(forms.ModelForm):
    class Meta:
        model = WantedPerson
        fields = ['name', 'crime', 'reward', 'image', 'details']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Describe the crime or details...'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'crime': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Crime committed'}),
            'reward': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Reward (optional)'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

def Reportwanted(request):
    if request.method == 'POST':
        # Status change form
        if 'status' in request.POST and 'person_id' in request.POST:
            person_id = request.POST.get('person_id')
            new_status = request.POST.get('status')
            try:
                person = WantedPerson.objects.get(id=person_id)
                if new_status in dict(WantedPerson.STATUS_CHOICES):
                    person.status = new_status
                    person.save()
                    messages.success(request, f"Status updated to {person.get_status_display()} for {person.name}.")
                else:
                    messages.error(request, 'Invalid status value.')
            except WantedPerson.DoesNotExist:
                messages.error(request, 'Wanted person not found.')
            return redirect('Reportwanted')
        # New wanted person form
        form = WantedPersonForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Wanted person reported successfully!')
            return redirect('Reportwanted')
    else:
        form = WantedPersonForm()
    wanted_people = WantedPerson.objects.all().order_by('-id')
    return render(request, 'Reportwanted.html', {'form': form, 'wanted_people': wanted_people})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login as auth_login, logout
from django import forms
from .models import News, Report, MissingPerson, WantedPerson, Tip, MissingGoods
from django.db.models import Q
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime
import json
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse

def home(request):
    return render(request, 'home.html')

def is_front_line_officer(user):
    return user.is_authenticated and user.user_type == 'front_line_officer'


@login_required(login_url='admin_login')
@user_passes_test(is_front_line_officer, login_url='admin_login')
def admin(request):
    from .models import Report, MissingPerson, Notification
    total_open = Report.objects.filter(status='open').count()
    total_investigating = Report.objects.filter(status='investigating').count()
    total_closed = Report.objects.filter(status='closed').count()
    total_missing = MissingPerson.objects.filter(status='missing').count()

    # Group by day for chart
    open_by_day = Report.objects.filter(status='open').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')
    investigating_by_day = Report.objects.filter(status='investigating').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')
    closed_by_day = Report.objects.filter(status='closed').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')

    # Build chart data: get all unique days
    all_days = set()
    for q in [open_by_day, investigating_by_day, closed_by_day]:
        all_days.update([str(item['day']) for item in q])
    all_days = sorted(all_days)

    open_dict = {str(item['day']): item['count'] for item in open_by_day}
    investigating_dict = {str(item['day']): item['count'] for item in investigating_by_day}
    closed_dict = {str(item['day']): item['count'] for item in closed_by_day}

    chart_labels = all_days
    chart_open = [open_dict.get(day, 0) for day in all_days]
    chart_investigating = [investigating_dict.get(day, 0) for day in all_days]
    chart_closed = [closed_dict.get(day, 0) for day in all_days]

    # Serialize to JSON for safe JS usage
    chart_labels_json = json.dumps(chart_labels)
    chart_open_json = json.dumps(chart_open)
    chart_investigating_json = json.dumps(chart_investigating)
    chart_closed_json = json.dumps(chart_closed)

    # Notifications for admin
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    # Gender distribution for missing persons (status='missing')
    gender_counts = (
        MissingPerson.objects
        .filter(status='missing')
        .values('gender')
        .annotate(count=Count('id'))
    )
    # Use display values for labels
    gender_display = dict(MissingPerson.GENDER_CHOICES)
    gender_labels = []
    gender_data = []
    for g in gender_counts:
        label = gender_display.get(g['gender'], g['gender'].capitalize() if g['gender'] else 'Unknown')
        gender_labels.append(label)
        gender_data.append(g['count'])

    return render(request, 'admin.html', {
        'total_open': total_open,
        'total_investigating': total_investigating,
        'total_closed': total_closed,
        'total_missing': total_missing,
        'chart_labels': chart_labels_json,
        'chart_open': chart_open_json,
        'chart_investigating': chart_investigating_json,
        'chart_closed': chart_closed_json,
        'notifications': notifications,
        'unread_count': unread_count,
        'gender_labels': json.dumps(gender_labels),
        'gender_data': json.dumps(gender_data),
    })

def is_investigating_officer(user):
    return user.is_authenticated and user.user_type == 'investigating_officer'

@login_required(login_url='admin_login')
@user_passes_test(is_investigating_officer, login_url='admin_login')
def investigator_dashboard(request):
    from .models import Report, MissingPerson, Notification
    total_open = Report.objects.filter(status='open').count()
    total_investigating = Report.objects.filter(status='investigating').count()
    total_closed = Report.objects.filter(status='closed').count()
    total_missing = MissingPerson.objects.filter(status='missing').count()

    # Group by day for chart
    open_by_day = Report.objects.filter(status='open').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')
    investigating_by_day = Report.objects.filter(status='investigating').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')
    closed_by_day = Report.objects.filter(status='closed').annotate(day=TruncDate('submitted_at')).values('day').annotate(count=Count('id')).order_by('day')

    # Build chart data: get all unique days
    all_days = set()
    for q in [open_by_day, investigating_by_day, closed_by_day]:
        all_days.update([str(item['day']) for item in q])
    all_days = sorted(all_days)

    open_dict = {str(item['day']): item['count'] for item in open_by_day}
    investigating_dict = {str(item['day']): item['count'] for item in investigating_by_day}
    closed_dict = {str(item['day']): item['count'] for item in closed_by_day}

    chart_labels = all_days
    chart_open = [open_dict.get(day, 0) for day in all_days]
    chart_investigating = [investigating_dict.get(day, 0) for day in all_days]
    chart_closed = [closed_dict.get(day, 0) for day in all_days]

    # Serialize to JSON for safe JS usage
    chart_labels_json = json.dumps(chart_labels)
    chart_open_json = json.dumps(chart_open)
    chart_investigating_json = json.dumps(chart_investigating)
    chart_closed_json = json.dumps(chart_closed)

    # Notifications for investigator_dashboard
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    # Gender distribution for missing persons (status='missing')
    gender_counts = (
        MissingPerson.objects
        .filter(status='missing')
        .values('gender')
        .annotate(count=Count('id'))
    )
    # Use display values for labels
    gender_display = dict(MissingPerson.GENDER_CHOICES)
    gender_labels = []
    gender_data = []
    for g in gender_counts:
        label = gender_display.get(g['gender'], g['gender'].capitalize() if g['gender'] else 'Unknown')
        gender_labels.append(label)
        gender_data.append(g['count'])

    return render(request, 'investigator_dashboard.html', {
        'total_open': total_open,
        'total_investigating': total_investigating,
        'total_closed': total_closed,
        'total_missing': total_missing,
        'chart_labels': chart_labels_json,
        'chart_open': chart_open_json,
        'chart_investigating': chart_investigating_json,
        'chart_closed': chart_closed_json,
        'notifications': notifications,
        'unread_count': unread_count,
        'gender_labels': json.dumps(gender_labels),
        'gender_data': json.dumps(gender_data),
    })

def about(request):
    return render(request, 'about.html')

def news(request):
    news_list = News.objects.all().order_by('-date')
    paginator = Paginator(news_list, 4)  # 4 news per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'news.html', {'page_obj': page_obj})

def services(request):
    return render(request, 'services.html')

def wanted_person(request):
    if request.method == 'POST' and 'tip_submit' in request.POST:
        person_id = request.POST.get('wanted_person_id')
        tip_text = request.POST.get('tip_text')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        if person_id and tip_text:
            try:
                wanted_person = WantedPerson.objects.get(id=person_id)
                tip = Tip.objects.create(wanted_person=wanted_person, tip_text=tip_text, is_anonymous=is_anonymous)
                # Create notification for all superusers
                from django.contrib.auth import get_user_model
                from .models import Notification
                User = get_user_model()
                admins = User.objects.filter(is_superuser=True)
                for admin in admins:
                    Notification.objects.create(user=admin, message=f"New tip submitted for {wanted_person.name}.")
                messages.success(request, 'Your tip has been submitted!')
            except WantedPerson.DoesNotExist:
                messages.error(request, 'Wanted person not found.')
        else:
            messages.error(request, 'Please provide your tip.')

    wanted_people = WantedPerson.objects.filter(status='at_large').order_by('-id')
    paginator = Paginator(wanted_people, 2)  # 4 per page for 2x4 grid
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'wanted_person.html', {'page_obj': page_obj})


def missing(request):
    missing_people = MissingPerson.objects.all().order_by('-date_reported')
    paginator = Paginator(missing_people, 4)  # 16 per page for 4x4 grid
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'missing.html', {'page_obj': page_obj})

def contact(request):
    return render(request, 'contact.html')

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'phone_number', 'gender', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match')
        return cleaned_data

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')  # Change 'home' to your home page url name
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'login.html')


import re

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['photo', 'date', 'title', 'description']
        widgets = {
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control bg-dark', 'accept': 'image/*'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control bg-dark'}),
            'title': forms.TextInput(attrs={'class': 'form-control bg-dark', 'placeholder': 'Enter news title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control bg-dark',
                'style': 'height: 150px;',
                'placeholder': 'Leave a description',
                'id': 'floatingTextarea'
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')

        # Require at least one letter in the title
        if not re.search(r'[A-Za-z]', title):
            raise forms.ValidationError("Title must contain at least one letter, not just numbers.")

        return title


def Postnews(request):
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'News posted successfully!')
            return redirect('Postnews')
    else:
        form = NewsForm()
    return render(request, 'Postnews.html', {'form': form})

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['report_type', 'file', 'link', 'description']
        widgets = {
            'report_type': forms.HiddenInput(),  # Hide the report_type select
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'id': 'id_file', 'style': 'display:none;'}),
            'link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Paste your link here'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your report', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['link'].required = False

def Sendreport(request):
    if request.method == 'POST':
        post = request.POST.copy()
        files = request.FILES.copy()
        if 'file' not in files and 'file' in request.FILES:
            files['file'] = request.FILES['file']
        # If report_type is 'video' and description is empty, set default description
        if post.get('report_type') == 'video' and not post.get('description'):
            post['description'] = 'Person with disabley'
        form = ReportForm(post, files)
        if form.is_valid():
            report = form.save(commit=False)
            if request.user.is_authenticated:
                report.user = request.user
            report.save()
            # Create notification for all superusers
            from django.contrib.auth import get_user_model
            from .models import Notification
            User = get_user_model()
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(user=admin, message=f"New report submitted: {report.get_report_type_display()}.")
            messages.success(request, 'Report submitted successfully!')
            return redirect('Sendreport')
    else:
        form = ReportForm()
    return render(request, 'Sendreport.html', {'form': form})

def Reportadmin(request):
    reports = Report.objects.filter(report_type__in=['photo', 'video', 'audio', 'link', 'file']).order_by('-submitted_at')

    # --- Active Reports Filtering ---
    active_reports = reports.exclude(status='closed').exclude(status='solved')
    active_case_id = request.GET.get('active_case_id', '').replace('#C-', '').strip()
    active_name = request.GET.get('active_name', '').strip()
    active_email = request.GET.get('active_email', '').strip()
    active_date = request.GET.get('active_date', '').strip()
    if active_case_id:
        if active_case_id.isdigit():
            active_reports = active_reports.filter(id=int(active_case_id))
        else:
            active_reports = active_reports.none()
    if active_name:
        active_reports = active_reports.filter(
            Q(user__first_name__icontains=active_name) | Q(user__last_name__icontains=active_name)
        )
    if active_email:
        active_reports = active_reports.filter(user__email__icontains=active_email)
    if active_date:
        try:
            date_obj = datetime.strptime(active_date, '%Y-%m-%d').date()
            active_reports = active_reports.filter(submitted_at__date=date_obj)
        except ValueError:
            pass

    # --- Archived Reports Filtering ---
    archived_reports = reports.filter(status__in=['closed', 'solved'])
    archive_case_id = request.GET.get('archive_case_id', '').replace('#C-', '').strip()
    archive_name = request.GET.get('archive_name', '').strip()
    archive_email = request.GET.get('archive_email', '').strip()
    archive_date = request.GET.get('archive_date', '').strip()
    if archive_case_id:
        if archive_case_id.isdigit():
            archived_reports = archived_reports.filter(id=int(archive_case_id))
        else:
            archived_reports = archived_reports.none()
    if archive_name:
        archived_reports = archived_reports.filter(
            Q(user__first_name__icontains=archive_name) | Q(user__last_name__icontains=archive_name)
        )
    if archive_email:
        archived_reports = archived_reports.filter(user__email__icontains=archive_email)
    if archive_date:
        try:
            date_obj = datetime.strptime(archive_date, '%Y-%m-%d').date()
            archived_reports = archived_reports.filter(submitted_at__date=date_obj)
        except ValueError:
            pass

    return render(request, 'Reportadmin.html', {
        'reports': active_reports,
        'archived_reports': archived_reports
    })

def solve_report(request, report_id):
    if request.method == 'POST':
        report = get_object_or_404(Report, id=report_id)
        new_status = request.POST.get('status')
        if new_status in ['open', 'investigating', 'closed']:
            report.status = new_status
            report.save()
            messages.success(request, f'Report status updated to {report.get_status_display()}!')
        else:
            messages.error(request, 'Invalid status value.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('Reportadmin')

# For explicit close action (if needed)
def close_report(request, report_id):
    if request.method == 'POST':
        report = get_object_or_404(Report, id=report_id)
        report.status = 'closed'
        report.save()
        messages.success(request, 'Report marked as Closed and archived!')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('Reportadmin')

def delete_report(request, report_id):
    if request.method == 'POST':
        report = get_object_or_404(Report, id=report_id)
        report.delete()
        messages.success(request, 'Report deleted successfully!')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('Reportadmin')


def admin_login(request):
    error = None
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            if user.is_superuser:
                auth_login(request, user)
                return redirect('Adminsettings')  # 👈 Superuser → Adminsettings page
            elif user.user_type == 'front_line_officer':
                auth_login(request, user)
                return redirect('admin')  # Front-line → Admin dashboard or appropriate page
            elif user.user_type == 'investigating_officer':
                auth_login(request, user)
                return redirect('investigator_dashboard')  # Investigator → Investigator dashboard
            else:
                error = 'Access denied. You are not authorized to access this page.'
        else:
            error = 'Invalid email or password.'

    return render(request, 'admin_login.html', {'error': error})

def admin_logout(request):
    logout(request)
    return redirect('home')


def Reportmissing(request):
    from .models import MissingPerson
    if request.method == 'POST':
        name = request.POST.get('name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        details = request.POST.get('details')
        status = request.POST.get('status')
        last_seen = request.POST.get('last_seen')
        image = request.FILES.get('image')
        errors = []
        if not name:
            errors.append('Name is required.')
        if not gender:
            errors.append('Gender is required.')
        if not details:
            errors.append('Details are required.')
        if not status:
            errors.append('Status is required.')
        if not last_seen:
            errors.append('Last Seen is required.')
        if errors:
            for error in errors:
                messages.error(request, error)
            # Pass reported_missing for table display
            reported_missing = MissingPerson.objects.all().order_by('-date_reported')
            return render(request, 'Reportmissing.html', {'reported_missing': reported_missing})
        person = MissingPerson(
            name=name,
            age=age or None,
            gender=gender,
            details=details,
            status=status,
            last_seen=last_seen
        )
        if image:
            person.image = image
        person.save()
        messages.success(request, 'Missing person reported successfully!')
        return redirect('Reportmissing')
    # Always pass reported_missing for table display
    reported_missing = MissingPerson.objects.all().order_by('-date_reported')
    return render(request, 'Reportmissing.html', {'reported_missing': reported_missing})

@require_POST
def update_missing_status(request):
    from .models import MissingPerson
    import json
    if not request.user.is_authenticated or not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        person_id = data.get('id')
        new_status = data.get('status')
        if not person_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)
        person = MissingPerson.objects.get(id=person_id)
        if new_status not in dict(MissingPerson.STATUS_CHOICES):
            return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
        person.status = new_status
        person.save()
        return JsonResponse({'success': True, 'status_display': person.get_status_display()})
    except MissingPerson.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Person not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


from django.contrib import messages

def is_admin(user):
    return user.is_superuser  # or customize this check as needed

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def Adminsettings(request):
    User = get_user_model()
    users = User.objects.all().order_by('-date_joined')
    edit_user = None

    if request.method == 'POST':
        # Create new user
        if 'create_user' in request.POST:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
            user_type = request.POST.get('user_type')
            is_superuser = request.POST.get('is_superuser') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'

            if not username or not email or not password or not user_type:
                messages.error(request, 'All fields including user type are required.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'A user with this email already exists.')
            else:
                user = User(
                    username=username,
                    email=email,
                    is_superuser=is_superuser,
                    is_staff=is_staff,
                    user_type=user_type
                )
                user.set_password(password)
                user.save()
                messages.success(request, 'User created successfully.')
                return redirect('Adminsettings')

        # Edit existing user
        elif 'edit_user_id' in request.POST:
            user_id = request.POST.get('edit_user_id')
            try:
                user = User.objects.get(id=user_id)
                user.username = request.POST.get('edit_username')
                user.email = request.POST.get('edit_email')
                user_type = request.POST.get('edit_user_type')
                user.is_superuser = request.POST.get('edit_is_superuser') == 'on'
                user.is_staff = request.POST.get('edit_is_staff') == 'on'
                password = request.POST.get('edit_password')

                if user_type:
                    user.user_type = user_type

                if password:
                    user.set_password(password)

                user.save()
                messages.success(request, 'User updated successfully.')
                return redirect('Adminsettings')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        # Delete user
        elif 'delete_user_id' in request.POST:
            user_id = request.POST.get('delete_user_id')
            try:
                user = User.objects.get(id=user_id)
                if user == request.user:
                    messages.error(request, 'You cannot delete your own account.')
                else:
                    user.delete()
                    messages.success(request, 'User deleted successfully.')
                return redirect('Adminsettings')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

    # Handle edit request from GET
    elif request.method == 'GET' and 'edit_user_id' in request.GET:
        try:
            edit_user = User.objects.get(id=request.GET.get('edit_user_id'))
        except User.DoesNotExist:
            edit_user = None

    return render(request, 'Adminsettings.html', {
        'users': users,
        'edit_user': edit_user
    })

class MissingGoodsForm(forms.ModelForm):
    class Meta:
        model = MissingGoods
        fields = ['name', 'category', 'description', 'image', 'status', 'last_seen']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the item...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'last_seen': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where was it last seen?'}),
        }

def Reportmissinggoods(request):
    if request.method == 'POST':
        # Handle status change for a good
        if 'status' in request.POST and 'item_id' in request.POST:
            item_id = request.POST.get('item_id')
            new_status = request.POST.get('status')
            try:
                item = MissingGoods.objects.get(id=item_id)
                if new_status in dict(MissingGoods.STATUS_CHOICES):
                    item.status = new_status
                    item.save()
                    messages.success(request, f"Status updated to {item.get_status_display()} for {item.name}.")
                else:
                    messages.error(request, 'Invalid status value.')
            except MissingGoods.DoesNotExist:
                messages.error(request, 'Missing goods not found.')
            return redirect('Reportmissinggoods')
        # Handle new report
        form = MissingGoodsForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Missing goods reported successfully!')
            return redirect('Reportmissinggoods')
    else:
        form = MissingGoodsForm()
    goods = MissingGoods.objects.all().order_by('-date_reported')
    return render(request, 'Reportmissinggoods.html', {'form': form, 'goods': goods})

def missinggoods(request):
    # Only show goods that are not marked as 'found' for public listing
    goods_qs = MissingGoods.objects.exclude(status='found').order_by('-date_reported')
    paginator = Paginator(goods_qs, 4)  # 4 goods per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # For backward compatibility, also pass all goods (including found) if needed elsewhere
    all_goods = MissingGoods.objects.all().order_by('-date_reported')
    return render(request, 'missinggoods.html', {'page_obj': page_obj, 'goods': all_goods})

@csrf_exempt
@login_required(login_url='admin_login')
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required(login_url='admin_login')
def notifications_center(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, 'notifications_center.html', {'notifications': notifications})