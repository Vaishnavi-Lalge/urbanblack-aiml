# Building ride-service

## Fix for "UUID cannot be converted to Long" compilation error

The ride-service depends on the `common` module. If you build from the `ride-service` directory only, Maven may use a stale `common` jar from your local repo, causing type mismatch errors.

**Always build from the backend root** so `common` is built first:

```bash
cd backend-infra/urbanblack-backend
mvn clean package -pl ride-service -am -DskipTests
```

- `-pl ride-service` = build ride-service
- `-am` = also make (build common first)
- `-DskipTests` = skip tests

Or build common first, then ride-service:

```bash
cd backend-infra/urbanblack-backend
mvn clean install -pl common -DskipTests
mvn clean package -pl ride-service -DskipTests
```
