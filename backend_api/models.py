import sqlalchemy
from sqlalchemy import Column, String, Boolean, Float, JSON
from .database import metadata
import uuid

# Function to generate UUIDs
def generate_uuid():
    return str(uuid.uuid4())

cameras = sqlalchemy.Table(
    "cameras",
    metadata,
    Column("id", String, primary_key=True, default=generate_uuid),
    Column("name", String, nullable=False),
    Column("url", String, nullable=False),
    Column("description", String, nullable=True),
    Column("policy_id", String, nullable=False), # Assuming this links to a Policy ID
    Column("model_settings_id", String, nullable=False), # Assuming this links to a ModelSettings ID
    Column("is_active", Boolean, default=True),
)

policies = sqlalchemy.Table(
    "policies",
    metadata,
    Column("id", String, primary_key=True, default=generate_uuid),
    Column("name", String, nullable=False),
    Column("policy_type", String, nullable=False),
    Column("parameters", JSON, nullable=False), # Storing Dict as JSON
)

model_settings = sqlalchemy.Table(
    "model_settings",
    metadata,
    Column("id", String, primary_key=True, default=generate_uuid),
    Column("name", String, nullable=False),
    Column("model_path", String, nullable=False),
    Column("confidence_threshold", Float, nullable=False),
    Column("iou_threshold", Float, nullable=False),
    Column("other_params", JSON, nullable=True), # Storing Dict as JSON
)
