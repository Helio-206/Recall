from typing import Literal

ProcessingStatus = Literal["pending", "processing", "completed", "failed"]
SourceType = Literal["single_video", "playlist", "channel"]
Platform = Literal["youtube", "coursera"]

PENDING: ProcessingStatus = "pending"
PROCESSING: ProcessingStatus = "processing"
COMPLETED: ProcessingStatus = "completed"
FAILED: ProcessingStatus = "failed"
