from app.core.database import Base, engine_shard1_replica, engine_shard2_replica
from app.models.document import Document

Base.metadata.create_all(bind=engine_shard1_replica)
Base.metadata.create_all(bind=engine_shard2_replica)
print("Tablas creadas en réplicas")