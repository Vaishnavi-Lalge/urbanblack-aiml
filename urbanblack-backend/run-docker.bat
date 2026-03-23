@echo off
echo Starting Urban Black Backend...

echo Building all services...
powershell -ExecutionPolicy Bypass -File build-all.ps1

if %errorlevel% neq 0 (
    echo Build failed!
    pause
    exit /b %errorlevel%
)

echo.
echo Starting Docker containers...
docker-compose up --build -d

echo.
echo Services should be starting up.
echo Eureka: http://localhost:8761
echo API Gateway: http://localhost:8080
echo Employee Service Swagger: http://localhost:8085/swagger-ui.html
echo.
pause
