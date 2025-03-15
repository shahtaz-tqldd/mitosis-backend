from rest_framework import serializers


class CreateProductSerializer(serializers.ModelSerializer):
  name = serializers.CharField(max_length=200)