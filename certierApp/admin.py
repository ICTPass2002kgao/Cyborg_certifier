from django.contrib import admin

from .models import userDocuments,CertifiedDocumentUpload,UserFaceVerification

# Register your models here.
admin.site.register(userDocuments)
admin.site.register(CertifiedDocumentUpload)
admin.site.register(UserFaceVerification)

