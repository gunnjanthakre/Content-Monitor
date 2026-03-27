from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Flag
from .serializers import FlagSerializer, FlagStatusUpdateSerializer


class FlagListView(APIView):
    def get(self, request: Request) -> Response:
        qs = Flag.objects.select_related('keyword', 'content_item').all()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = FlagSerializer(qs, many=True)
        return Response(serializer.data)


class FlagDetailView(APIView):
    def _get_flag(self, pk: int):
        try:
            return Flag.objects.select_related('keyword', 'content_item').get(pk=pk)
        except Flag.DoesNotExist:
            return None

    def get(self, request: Request, pk: int) -> Response:
        flag = self._get_flag(pk)
        if flag is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(FlagSerializer(flag).data)

    def patch(self, request: Request, pk: int) -> Response:
        flag = self._get_flag(pk)
        if flag is None:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = FlagStatusUpdateSerializer(flag, data=request.data, partial=True)
        if serializer.is_valid():
            updated_flag = serializer.save()
            return Response(FlagSerializer(updated_flag).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)