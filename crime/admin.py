from django.contrib import admin
from .models import (
    UserCustom, CrimeCase, EvidenceFile, Announcement, WantedPerson, Tip, MissingPerson, MissingPersonReport,
    PublicCrimeReport, Notification, AnonymousTip, Complaint, CaseSuggestion, News, Report, MissingGoods
)

admin.site.register(UserCustom)
admin.site.register(CrimeCase)
admin.site.register(EvidenceFile)
admin.site.register(Announcement)
admin.site.register(WantedPerson)
admin.site.register(Tip)
admin.site.register(MissingPerson)
admin.site.register(MissingGoods)
admin.site.register(MissingPersonReport)
admin.site.register(PublicCrimeReport)
admin.site.register(Notification)
admin.site.register(AnonymousTip)
admin.site.register(Complaint)
admin.site.register(CaseSuggestion)
admin.site.register(News)
admin.site.register(Report)
