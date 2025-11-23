from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from services.departments.department_services import DepartmentClient
from services.dependencies.dependencies import get_department_service
from services.dependencies.dependencies_repo import request_context

departments_router = APIRouter(dependencies=[Depends(request_context)])


@departments_router.get(
    "/update-departments",
    summary="Update departments",
    description="Update departments from Bitrix24",
)  # type: ignore
async def update_departments(
    department_client: DepartmentClient = Depends(get_department_service),
) -> JSONResponse:
    result = await department_client.import_from_bitrix()
    return JSONResponse(
        status_code=200,
        content={"updated": len(result)},
    )
