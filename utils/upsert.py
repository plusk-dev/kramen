import uuid
from fastembed import LateInteractionTextEmbedding, SparseTextEmbedding, TextEmbedding
from qdrant_client import models
from schemas.raapi_schemas.upsert import UpsertSchema
from config import DENSE_EMBEDDING_MODEL, LATE_EMBEDDING_MODEL, SPARSE_EMBEDDING_MODEL, qdrant_client


async def upsert_vector(request: UpsertSchema):
    existing_collections = qdrant_client.get_collections().collections
    exists = False
    for collection in existing_collections:
        if collection.name == request.integration_id:
            exists = True
            break

    dense_embedding_model = TextEmbedding(
        f"sentence-transformers/{DENSE_EMBEDDING_MODEL}")
    bm25_embedding_model = SparseTextEmbedding(
        f"Qdrant/{SPARSE_EMBEDDING_MODEL}")
    late_interaction_embedding_model = LateInteractionTextEmbedding(
        f"colbert-ir/{LATE_EMBEDDING_MODEL}")

    dense_vector = list(dense_embedding_model.passage_embed(request.text))
    sparse_vector = list(bm25_embedding_model.passage_embed(request.text))
    late_vector = list(
        late_interaction_embedding_model.passage_embed(request.text))

    if not exists:
        qdrant_client.create_collection(
            request.integration_id,
            vectors_config={
                DENSE_EMBEDDING_MODEL: models.VectorParams(
                    size=len(dense_vector[0]),
                    distance=models.Distance.COSINE,
                ),
                LATE_EMBEDDING_MODEL: models.VectorParams(
                    size=128,
                    distance=models.Distance.COSINE,
                    multivector_config=models.MultiVectorConfig(
                        comparator=models.MultiVectorComparator.MAX_SIM,
                    )
                ),
            },
            sparse_vectors_config={
                SPARSE_EMBEDDING_MODEL: models.SparseVectorParams(
                    modifier=models.Modifier.IDF,
                )
            }
        )

    metadata = request.metadata
    metadata['text'] = request.text
    new_point = qdrant_client.upsert(request.integration_id, points=[
        models.PointStruct(
            id=str(uuid.uuid4()),
            vector={
                DENSE_EMBEDDING_MODEL: dense_vector[0].tolist(),
                SPARSE_EMBEDDING_MODEL: sparse_vector[0].as_object(),
                LATE_EMBEDDING_MODEL: late_vector[0].tolist()
            },
            payload=metadata
        )
    ])

    return new_point
