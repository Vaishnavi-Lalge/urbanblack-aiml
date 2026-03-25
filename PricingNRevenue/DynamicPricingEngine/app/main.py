from fastapi import FastAPI
from app.api.endpoints import pricing, driver

app = FastAPI(title="Urban Black Dynamic Pricing Engine",
              description="Urban Black MVP Pricing & Revenue Domain API",
              version="1.0.0")

app.include_router(pricing.router, prefix="/api/v1/pricing", tags=["Pricing"])
app.include_router(driver.router, prefix="/api/v1/driver", tags=["Driver"])

@app.on_event("startup")
async def startup_event():
    # Initialize Redis & Kafka connections here
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # Close connections
    pass

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "dynamic-pricing-engine"}
