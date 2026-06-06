"""workers/ — Background task workers for activia-trace.

Workers are async tasks that run as background tasks within the FastAPI
process lifecycle. They are started in the lifespan startup and gracefully
stopped at shutdown.
"""
