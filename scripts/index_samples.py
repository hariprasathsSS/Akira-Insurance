"""Index sample policy PDFs into database and Qdrant."""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models.document import PolicyDocument, PolicyDocumentVersion
from app.db.models.job import BackgroundJob
from app.db.models.user import User
from app.db.session import get_session_factory
from app.rag.ingestion import run_ingestion_job


async def index_samples():
    settings = get_settings()
    factory = get_session_factory()
    async with factory() as session:
        admin = (
            await session.execute(select(User).where(User.public_id == "U-901"))
        ).scalar_one()
        docs = (await session.execute(select(PolicyDocument))).scalars().all()

        sample_dir = os.path.join(os.getcwd(), "storage", "sample_policies")
        file_map = {
            "DOC-HEALTH-001": "health_guard_basic_v1.pdf",
            "DOC-MOTOR-001": "motor_drivecare_gold_v1.pdf",
            "DOC-HOME-001": "home_protect_elite_v1.pdf",
        }

        for doc in docs:
            fname = file_map.get(doc.public_id)
            if not fname:
                continue
            pdf_path = os.path.join(sample_dir, fname)
            if not os.path.exists(pdf_path):
                print(f"File not found: {pdf_path}")
                continue

            # Check if version already exists
            existing_ver = (
                await session.execute(
                    select(PolicyDocumentVersion).where(
                        PolicyDocumentVersion.document_id == doc.id,
                        PolicyDocumentVersion.version_number == 1,
                    )
                )
            ).scalar_one_or_none()

            if existing_ver is None:
                print(f"Creating version for {doc.public_id} from {pdf_path}...")
                ver = PolicyDocumentVersion(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    version_number=1,
                    original_filename=fname,
                    stored_path=pdf_path,
                    sha256="sample-" + doc.public_id,
                    mime_type="application/pdf",
                    file_size_bytes=os.path.getsize(pdf_path),
                    status="uploaded",
                    is_active=True,
                    qdrant_collection=settings.QDRANT_COLLECTION,
                    uploaded_by_user_id=admin.id,
                )
                session.add(ver)
                job = BackgroundJob(
                    id=uuid.uuid4(),
                    public_id=f"JOB-{uuid.uuid4().hex[:12].upper()}",
                    job_type="policy_ingestion",
                    status="queued",
                    requested_by_user_id=admin.id,
                    resource_id=ver.id,
                )
                session.add(job)
                await session.commit()
            else:
                ver = existing_ver
                job = BackgroundJob(
                    id=uuid.uuid4(),
                    public_id=f"JOB-{uuid.uuid4().hex[:12].upper()}",
                    job_type="policy_ingestion",
                    status="queued",
                    requested_by_user_id=admin.id,
                    resource_id=ver.id,
                )
                session.add(job)
                await session.commit()

            print(f"Running ingestion for {doc.public_id}...")
            await run_ingestion_job(
                job_id=job.id,
                version_id=ver.id,
                stored_path=pdf_path,
                collection_name=settings.QDRANT_COLLECTION,
                metadata={
                    "document_id": str(doc.id),
                    "document_public_id": doc.public_id,
                    "policy_type": doc.policy_type,
                    "plan_tier": doc.plan_tier,
                    "version_number": 1,
                    "document_title": doc.title,
                },
            )
            print(f"Successfully ingested {doc.public_id} ({doc.title})!")


if __name__ == "__main__":
    asyncio.run(index_samples())
