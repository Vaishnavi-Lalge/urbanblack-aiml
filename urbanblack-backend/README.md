# Urban Black Backend - Microservices Architecture

## Overview
Urban Black Backend is a microservices-based application built with Spring Boot and Spring Cloud. The architecture includes:

- **Eureka Server** - Service Discovery (Port: 8761)
- **API Gateway** - Single entry point for all services (Port: 8080)
- **Auth Service** - Authentication and Authorization (Port: 8081)
- **Employee Details Service** - Employee management (Port: 8085)
- **PostgreSQL** - Database (Port: 5432)
- **Kafka & Zookeeper** - Message broker

## Prerequisites
- Java 17 or higher
- Maven 3.6+
- Docker & Docker Compose
- PostgreSQL (if running locally without Docker)

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │ :8080
│   (Port 8080)   │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Auth Service │ │   Employee   │ │    Other     │
│  (Port 8081) │ │   Details    │ │   Services   │
│              │ │  (Port 8085) │ │              │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
                ┌──────────────┐
                │  PostgreSQL  │
                │  (Port 5432) │
                └──────────────┘
```

All services register with **Eureka Server** (Port 8761) for service discovery.

## Running with Docker (Recommended)

### Step 1: Build All Services
```powershell
# Run the build script
.\build-all.ps1
```

Or manually:
```powershell
# Build parent and common module
mvn clean install -DskipTests

# Build each service
cd eureka-server
mvn clean package -DskipTests
cd ..

cd auth-service
mvn clean package -DskipTests
cd ..

cd EmployeeDetails-Service
mvn clean package -DskipTests
cd ..

cd api-gateway
mvn clean package -DskipTests
cd ..
```

### Step 2: Start All Services with Docker Compose
```powershell
docker-compose up --build
```

To run in detached mode:
```powershell
docker-compose up -d --build
```

### Step 3: Verify Services
- **Eureka Dashboard**: http://localhost:8761
- **API Gateway**: http://localhost:8080
- **Auth Service Swagger**: http://localhost:8081/swagger-ui.html
- **Employee Details Service Swagger**: http://localhost:8085/swagger-ui.html

### Stop All Services
```powershell
docker-compose down
```

To remove volumes as well:
```powershell
docker-compose down -v
```

## Running Locally (Without Docker)

### Prerequisites
1. PostgreSQL running on localhost:5432
2. Create databases:
   ```sql
   CREATE DATABASE urbanblack;
   CREATE DATABASE employee_details_db;
   ```

### Update Configuration
Update `application.yaml` in each service to use `localhost` instead of Docker service names:

**For Employee Details Service:**
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/employee_details_db

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
```

### Start Services in Order

1. **Start Eureka Server**
   ```powershell
   cd eureka-server
   mvn spring-boot:run
   ```

2. **Start Auth Service**
   ```powershell
   cd auth-service
   mvn spring-boot:run
   ```

3. **Start Employee Details Service**
   ```powershell
   cd EmployeeDetails-Service
   mvn spring-boot:run
   ```

4. **Start API Gateway**
   ```powershell
   cd api-gateway
   mvn spring-boot:run
   ```

## Employee Details Service

### Features
- Create new employee records
- Retrieve employee details by ID
- Manage employee documents (Aadhaar, Driving License)
- Track employee education and bank details

### API Endpoints

All endpoints are accessible through the API Gateway at `http://localhost:8080/employee-details-service/api/employees`

#### Create Employee
```http
POST /api/employees
Content-Type: application/json

{
  "fullName": "John Doe",
  "email": "john.doe@example.com",
  "mobile": "9876543210",
  "accountStatus": "ACTIVE"
}
```

#### Get Employee by ID
```http
GET /api/employees/{id}
```

### Swagger Documentation
Access the interactive API documentation at:
- **Direct**: http://localhost:8085/swagger-ui.html
- **Via Gateway**: http://localhost:8080/employee-details-service/swagger-ui.html

## Database Schema

### Employee Details Database
The `employee_details_db` contains the following tables:
- `employees` - Main employee information
- `aadhaar` - Aadhaar card details
- `aadhaar_address` - Address from Aadhaar
- `driving_license` - Driving license details
- `employee_education` - Education qualifications
- `bank_details` - Bank account information

## Configuration

### Environment Variables
You can override configuration using environment variables:

```yaml
SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/employee_details_db
SPRING_DATASOURCE_USERNAME: postgres
SPRING_DATASOURCE_PASSWORD: root
EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server:8761/eureka/
```

### JWT Configuration (Auth Service)
```yaml
jwt:
  secret: urbanblacksecretkeyurbanblacksecretkey123456
  expiration: 86400000
  access-expiration: 86400000
  refresh-expiration: 604800000
```

## Troubleshooting

### Service Not Registering with Eureka
1. Check if Eureka Server is running: http://localhost:8761
2. Verify network connectivity between services
3. Check service logs for connection errors

### Database Connection Issues
1. Verify PostgreSQL is running
2. Check database credentials in `application.yaml`
3. Ensure databases are created

### Port Already in Use
```powershell
# Find process using port
netstat -ano | findstr :8085

# Kill the process
taskkill /PID <process_id> /F
```

## Development

### Adding a New Service
1. Create service module
2. Add Eureka Client dependency
3. Configure `application.yaml` with service name and Eureka URL
4. Create Dockerfile
5. Add service to `docker-compose.yml`
6. Update `build-all.ps1`

### Testing APIs
Use Swagger UI for interactive API testing:
- Employee Details Service: http://localhost:8085/swagger-ui.html

Or use curl:
```powershell
# Create employee
curl -X POST http://localhost:8085/api/employees `
  -H "Content-Type: application/json" `
  -d '{
    "fullName": "John Doe",
    "email": "john.doe@example.com",
    "mobile": "9876543210",
    "accountStatus": "ACTIVE"
  }'

# Get employee
curl http://localhost:8085/api/employees/1
```

## Technology Stack
- **Spring Boot** 3.5.9
- **Spring Cloud** 2025.0.1
- **Java** 17
- **PostgreSQL** 15
- **Kafka** 7.5.0
- **Docker** & Docker Compose
- **Swagger/OpenAPI** 3.0

## License
© 2026 Urban Black. All rights reserved.
