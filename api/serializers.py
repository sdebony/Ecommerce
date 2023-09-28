from rest_framework import serializers


from accounts.models import AccountDirecciones

class DireccionesSerializer(serializers.ModelSerializer):

    class Meta:
        model=AccountDirecciones
        fields='__all__'
