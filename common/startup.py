import logging

logger = logging.getLogger("startup")


def _patch_scheduler_endpoint():
    import api
    from common.deps import require_auth
    from fastapi import Depends, HTTPException
    from scheduler.generator import generate_schedule
    from scheduler.models import ScheduleOutput, ScheduleRequest

    @api.app.post("/scheduler/generate")
    async def scheduler_generate(
        req: ScheduleRequest,
        user: dict = Depends(require_auth),
    ):
        try:
            result = await generate_schedule(req)
            return ScheduleOutput(**result.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("Patched /scheduler/generate endpoint")


_patch_scheduler_endpoint()
