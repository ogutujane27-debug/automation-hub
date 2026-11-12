from rest_framework import serializers, viewsets

from .models import EmailLog
from .permissions import AdminOnly


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'


class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EmailLogSerializer
    permission_classes = [AdminOnly]

    def get_queryset(self):
        qs = EmailLog.objects.all()
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs