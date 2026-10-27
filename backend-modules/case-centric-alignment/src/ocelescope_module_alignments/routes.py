from fastapi import APIRouter, HTTPException
from ocelescope import PetriNet
from ocelescope_backend.app.dependencies import ApiOcel, ApiSession
from ocelescope_backend.app.sse_manager import ErrorNotification, sse_manager
from pydantic import BaseModel

from ocelescope_module_alignments.models.alignment import AlignmentsResponse
from ocelescope_module_alignments.utils.compute_alignments import (
    AlignmentComputationError,
    compute_alignments,
)

router = APIRouter()


@router.get("/{ocel_id}/alignments", operation_id="get_alignments")
def get_alignments(
    ocel: ApiOcel, session: ApiSession, object_type: str, resource_id: str | None = None
) -> AlignmentsResponse:
    try:
        petri_net = session.load_resource(resource_id, PetriNet) if resource_id else None

        return compute_alignments(ocel, object_type, petri_net)
    except AlignmentComputationError as e:
        sse_manager.send_safe(
            session_id=session.id,
            message=ErrorNotification(
                type="error",
                title="Alignment computation failed",
                message=str(e),
                trace=e.trace,
            ),
        )
        raise HTTPException(status_code=422, detail=str(e)) from e


@router.get("/{ocel_id}/objects/types", operation_id="objectTypes")
def get_object_types(ocel: ApiOcel) -> list[str]:
    return ocel.objects.types

@router.get("/ocpn/schemaHash", operation_id="ocpnSchemaHash")
def get_ocpn_schema_hash() -> str:
    return PetriNet.get_schema_hash()