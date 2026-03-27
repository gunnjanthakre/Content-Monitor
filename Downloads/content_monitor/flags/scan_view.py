from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from services.scan import ScanService


class ScanView(APIView):
    def post(self, request: Request) -> Response:
        source = request.data.get("source", "mock")
        allowed_sources = ["mock"]
        if source not in allowed_sources:
            return Response(
                {"detail": f"Unknown source '{source}'. Allowed: {allowed_sources}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        service = ScanService(source=source)
        result = service.run()
        return Response(result, status=status.HTTP_200_OK)