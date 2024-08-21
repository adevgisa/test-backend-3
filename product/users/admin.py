from django.contrib import admin

from .models import Balance

@admin.register(Balance)
class BalanceAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super(BalanceAdmin, self).get_readonly_fields(
            request,
            obj
        )

        if obj:
            return readonly_fields + ['value']

        return readonly_fields
