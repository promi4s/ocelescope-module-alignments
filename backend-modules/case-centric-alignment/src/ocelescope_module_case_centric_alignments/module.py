from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version

from ocelescope_module_case_centric_alignments.routes import router


class CaseCentricAlignments(Module):
    meta = ModuleMeta(key="caseCentricAlignments", version=Version("1.0"))

    def create_app(self) -> FastAPI:
        app = FastAPI(title="Case-Centric Alignments", version=str(self.meta.version))
        app.include_router(router)
        return app
