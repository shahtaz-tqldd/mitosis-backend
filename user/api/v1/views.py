from rest_framework import generics, permissions
from user.models import CustomUser
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from ..serializers import CreateUserSerializer, GetUserListSerializer

class CreateNewUserView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CreateUserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        user_data = CreateUserSerializer(user).data

        return Response(
                {
                    "status": HTTP_201_CREATED,
                    "success": True,
                    "message": "New User Created!",
                    "data ": user_data
                },
                status=HTTP_201_CREATED
            )

class GetUserListView(generics.ListAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = GetUserListSerializer
    # permission_classes = [permissions.IsAuthenticated]
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "status":HTTP_200_OK,
                "success": True,
                "message":"User data fetched!",
                "data": serializer.data
            }, 
            status= HTTP_200_OK
        )
