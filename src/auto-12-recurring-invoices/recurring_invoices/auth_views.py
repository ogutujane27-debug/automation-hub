from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, authentication_classes, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .audit import record
from .permissions import role_of


class LoginThrottle(AnonRateThrottle):
    scope = 'login'


@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login_view(request):
    username = str(request.data.get('username', ''))
    user = authenticate(username=username, password=request.data.get('password', ''))
    if user is None:
        known = User.objects.filter(username=username).first()
        record(request, 'login_failed', None, {'username_tried': username[:150]}, user=known)
        return Response({'error': 'Wrong username or password.'}, status=status.HTTP_400_BAD_REQUEST)
    role = role_of(user)
    if role is None:
        record(request, 'login_refused_no_role', None, {}, user=user)
        return Response({'error': 'Your account has no role yet. Ask an Admin.'}, status=status.HTTP_403_FORBIDDEN)
    token, _ = Token.objects.get_or_create(user=user)
    record(request, 'login', None, {'role': role}, user=user)
    return Response({'token': token.key, 'username': user.username, 'role': role})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    record(request, 'logout')
    Token.objects.filter(user=request.user).delete()
    return Response({'detail': 'Logged out.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({'username': request.user.username, 'role': role_of(request.user)})
