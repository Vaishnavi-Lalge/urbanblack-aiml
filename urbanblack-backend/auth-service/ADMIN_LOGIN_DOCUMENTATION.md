# Urban Black Admin Login System Documentation (Hardcoded JWT)

This document provides a comprehensive overview of the hardcoded Admin Authentication system implemented for the Urban Black Auth Service.

## 1. Project Folder Structure
```text
src/main/java/com/urbanblack/auth/
├── config/
│   ├── PasswordConfig.java       # BCrypt Password Encoder bean
│   └── SecurityConfig.java       # Spring Security Filter Chain
├── controller/
│   └── AdminController.java      # Login API Endpoint
├── dto/
│   ├── AdminLoginRequest.java    # Login Request Body
│   └── AuthResponse.java         # JWT Response Body
├── exception/
│   ├── ErrorResponse.java        # Standard Error Format
│   ├── GlobalExceptionHandler.java # Error Interceptor
│   └── InvalidCredentialsException.java # Custom Auth Exception
├── security/
│   ├── JwtAuthenticationFilter.java # JWT Filter for every request
│   └── JwtUtils.java             # JWT generation and parsing
└── service/
    └── AdminService.java         # Hardcoded login logic
```

## 2. Admin Credentials (Hardcoded)
- **Email:** `admin@urbanblack.com`
- **Password:** `Admin@123`
- **Encryption:** BCrypt (The service stores the hash and verifies using `PasswordEncoder`)

## 3. API Specification

### Login Request
- **URL:** `POST /api/v1/auth/admin/login`
- **Body:**
```json
{
  "email": "admin@urbanblack.com",
  "password": "Admin@123"
}
```

### Successful Response
- **Status:** `200 OK`
- **Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "role": "ADMIN",
  "email": "admin@urbanblack.com"
}
```

### Error Response (Wrong Credentials)
- **Status:** `401 Unauthorized`
- **Body:**
```json
{
  "status": 401,
  "message": "Invalid email or password",
  "timestamp": "2024-05-20T10:30:00"
}
```

## 4. Authentication Flow
1. **Request:** Admin sends credentials via JSON to `/api/v1/auth/admin/login`.
2. **Controller:** `AdminController` receives the request and validates fields.
3. **Service:** `AdminService` checks if the email matches the hardcoded value.
4. **Verification:** `AdminService` uses `BCryptPasswordEncoder` to compare the raw password with the hardcoded hash.
5. **JWT Generation:** If valid, `JwtUtils` generates a signed token containing the email and "ADMIN" role.
6. **Response:** The controller returns the JWT token and user info.
7. **Subsequent Requests:** The client includes the token in the `Authorization: Bearer <token>` header.
8. **Interception:** `JwtAuthenticationFilter` intercepts the request, validates the token, and sets the Security Context.

## 5. Why Hardcoded Admin?
- **Bootstrapping:** Ideal for initial development or setup when no DB is available yet.
- **Simplicity:** Eliminates the need for user management UI or migrations for a single super-user.
- **Security Control:** Prevents "forgot password" or "signup" vulnerabilities for sensitive admin accounts.

## 6. Security Risks
- **No Password Rotation:** Changing the password requires a code redeployment.
- **Source Code Leak:** If the code is leaked, the encrypted password hash (and possibly secret keys) are exposed.
- **Single Point of Failure:** Only one hardcoded account exists; if compromised, there are no other admin logs to track individual actions.

## 7. Migration to DB-based System
To migrate this to a database-backed system:
1. **Create Table:** Add an `admins` table or use existing `users` table with a `ROLE_ADMIN` flag.
2. **AdminRepository:** Create a JPA repository to find users by email.
3. **AdminDetailsService:** Implement `UserDetailsService` to load admin details from the DB.
4. **Update AdminService:** Change `ADMIN_EMAIL` and `ADMIN_PASSWORD_HASH` checks to a repository lookup:
   ```java
   Admin admin = adminRepository.findByEmail(request.getEmail())
       .orElseThrow(() -> new InvalidCredentialsException("User not found"));
   ```

## 8. Development Notes
Ensure the following properties are set in your `application.properties` or `application.yml`:
```properties
jwt.secret=404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970
jwt.expiration=86400000
```
