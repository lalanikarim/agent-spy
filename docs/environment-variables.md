# Agent Spy Environment Variables Documentation

## Overview

This document provides a comprehensive overview of all environment variables used in the Agent Spy project, including their purpose, usage, and configuration details. The project consists of a backend (Python/FastAPI) and frontend (React/TypeScript) with various integration points.

## Table of Contents

1. [Backend Environment Variables](#backend-environment-variables)
2. [Frontend Environment Variables](#frontend-environment-variables)
3. [Test Environment Variables](#test-environment-variables)
4. [External Service Integration](#external-service-integration)
5. [Docker Configuration](#docker-configuration)
6. [Redundancies and Overlaps](#redundancies-and-overlaps)
7. [Security Concerns](#security-concerns)
8. [Recommendations](#recommendations)

## Backend Environment Variables

### Application Settings

| Variable      | Type    | Default       | Description                                               | Usage                                                                               |
| ------------- | ------- | ------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `ENVIRONMENT` | string  | "development" | Environment type (development, staging, production, test) | Used in `src/core/config.py` for environment validation and conditional behavior    |
| `DEBUG`       | boolean | false         | Enable debug mode                                         | Used in `src/core/config.py` and `src/main.py` for debug logging and error handling |

### Server Configuration

| Variable | Type    | Default   | Description                    | Usage                                                             |
| -------- | ------- | --------- | ------------------------------ | ----------------------------------------------------------------- |
| `HOST`   | string  | "0.0.0.0" | Server host address (internal) | Used in `src/core/config.py` and `src/main.py` for server binding |
| `PORT`   | integer | 8000      | Server port (internal, fixed)  | Used in `src/core/config.py` and `src/main.py` for server binding |
| `RELOAD` | boolean | false     | Auto-reload on code changes    | Used in `src/main.py` for development server                      |

### External Port Mapping

| Variable                 | Type    | Default     | Description                   | Usage                                            |
| ------------------------ | ------- | ----------- | ----------------------------- | ------------------------------------------------ |
| `BACKEND_EXTERNAL_PORT`  | integer | 8000        | External port for backend API | Used in Docker Compose for external port mapping |
| `FRONTEND_EXTERNAL_PORT` | integer | 3000        | External port for frontend    | Used in Docker Compose for external port mapping |
| `OTLP_EXTERNAL_PORT`     | integer | 4317        | External port for OTLP gRPC   | Used in Docker Compose for external port mapping |
| `BACKEND_HOST`           | string  | "localhost" | Backend hostname for frontend | Used by frontend to connect to backend           |

### Database Configuration

#### Core Database Settings

| Variable             | Type    | Default                             | Description                          | Usage                                                                               |
| -------------------- | ------- | ----------------------------------- | ------------------------------------ | ----------------------------------------------------------------------------------- |
| `DATABASE_TYPE`      | string  | "sqlite"                            | Database type (sqlite or postgresql) | Used in `src/core/config.py` and `src/core/database.py` for database initialization |
| `DATABASE_URL`       | string  | "sqlite+aiosqlite:///./agentspy.db" | Database connection URL              | Used in `src/core/config.py` and `src/core/database.py` for database connection     |
| `DATABASE_ECHO`      | boolean | false                               | Echo SQL queries                     | Used in `src/core/database.py` for SQL logging                                      |
| `DATABASE_POOL_SIZE` | integer | 20                                  | Connection pool size                 | Used in `src/core/database.py` for connection management                            |

#### PostgreSQL-Specific Settings

| Variable                            | Type    | Default         | Description                | Usage                                                                         |
| ----------------------------------- | ------- | --------------- | -------------------------- | ----------------------------------------------------------------------------- |
| `DATABASE_HOST` / `DB_HOST`         | string  | "localhost"     | PostgreSQL host            | Used in `src/core/config.py` for database URL construction                    |
| `DATABASE_PORT` / `DB_PORT`         | integer | 5432            | PostgreSQL port            | Used in `src/core/config.py` for database URL construction                    |
| `DATABASE_NAME` / `DB_NAME`         | string  | "agentspy"      | PostgreSQL database name   | Used in `src/core/config.py` for database URL construction                    |
| `DATABASE_USER` / `DB_USER`         | string  | "agentspy_user" | PostgreSQL username        | Used in `src/core/config.py` for database URL construction                    |
| `DATABASE_PASSWORD` / `DB_PASSWORD` | string  | ""              | PostgreSQL password        | Used in `src/core/config.py` for database URL construction                    |
| `DATABASE_SSL_MODE`                 | string  | "prefer"        | PostgreSQL SSL mode        | Used in `src/core/config.py` and `src/core/database.py` for SSL configuration |
| `DATABASE_MAX_CONNECTIONS`          | integer | 20              | PostgreSQL max connections | Used in `src/core/database.py` for connection pool configuration              |

### API Configuration

| Variable          | Type    | Default                                       | Description                              | Usage                                                         |
| ----------------- | ------- | --------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------- |
| `API_PREFIX`      | string  | "/api/v1"                                     | API route prefix                         | Used in `src/core/config.py` for API routing                  |
| `API_TITLE`       | string  | "Agent Spy API"                               | API documentation title                  | Used in `src/main.py` for FastAPI app configuration           |
| `API_DESCRIPTION` | string  | "LangSmith-compatible observability layer..." | API documentation description            | Used in `src/main.py` for FastAPI app configuration           |
| `REQUIRE_AUTH`    | boolean | false                                         | Require authentication for all endpoints | Used in `src/core/config.py` for authentication configuration |
| `API_KEYS`        | string  | null                                          | Comma-separated list of valid API keys   | Used in `src/core/config.py` for API key validation           |

### CORS Configuration

| Variable           | Type        | Default | Description                        | Usage                                                   |
| ------------------ | ----------- | ------- | ---------------------------------- | ------------------------------------------------------- |
| `CORS_ORIGINS`     | string/list | ["*"]   | Allowed CORS origins               | Used in `src/main.py` for CORS middleware configuration |
| `CORS_CREDENTIALS` | boolean     | true    | Allow credentials in CORS requests | Used in `src/main.py` for CORS middleware configuration |
| `CORS_METHODS`     | string/list | ["*"]   | Allowed CORS methods               | Used in `src/main.py` for CORS middleware configuration |
| `CORS_HEADERS`     | string/list | ["*"]   | Allowed CORS headers               | Used in `src/main.py` for CORS middleware configuration |

### OpenTelemetry (OTLP) Configuration

#### OTLP Receiver Settings

| Variable                                    | Type    | Default      | Description               | Usage                                                              |
| ------------------------------------------- | ------- | ------------ | ------------------------- | ------------------------------------------------------------------ |
| `OTLP_GRPC_ENABLED`                         | boolean | true         | Enable OTLP gRPC receiver | Used in `src/main.py` for OTLP server initialization               |
| `OTLP_GRPC_HOST` / `BACKEND_OTLP_GRPC_HOST` | string  | "0.0.0.0"    | OTLP gRPC server host     | Used in `src/otel/receiver/grpc_server.py` for gRPC server binding |
| `OTLP_GRPC_PORT` / `BACKEND_OTLP_GRPC_PORT` | integer | 4317         | OTLP gRPC server port     | Used in `src/otel/receiver/grpc_server.py` for gRPC server binding |
| `OTLP_HTTP_ENABLED`                         | boolean | true         | Enable OTLP HTTP receiver | Used in `src/main.py` for HTTP server configuration                |
| `OTLP_HTTP_PATH`                            | string  | "/v1/traces" | OTLP HTTP endpoint path   | Used in `src/main.py` for HTTP server routing                      |

#### OTLP Forwarder Settings

| Variable                      | Type    | Default               | Description                            | Usage                                            |
| ----------------------------- | ------- | --------------------- | -------------------------------------- | ------------------------------------------------ |
| `OTLP_FORWARDER_ENABLED`      | boolean | false                 | Enable OTLP forwarder                  | Used in `src/api/runs.py` for trace forwarding   |
| `OTLP_FORWARDER_ENDPOINT`     | string  | ""                    | OTLP forwarder endpoint URL            | Used in `src/api/runs.py` for trace forwarding   |
| `OTLP_FORWARDER_PROTOCOL`     | string  | "grpc"                | OTLP forwarder protocol (http or grpc) | Used in `src/core/config.py` for forwarder setup |
| `OTLP_FORWARDER_SERVICE_NAME` | string  | "agent-spy-forwarder" | Service name for forwarded traces      | Used in `src/api/runs.py` for trace forwarding   |
| `OTLP_FORWARDER_TIMEOUT`      | integer | 30                    | OTLP forwarder timeout in seconds      | Used in `src/api/runs.py` for trace forwarding   |
| `OTLP_FORWARDER_RETRY_COUNT`  | integer | 3                     | OTLP forwarder retry count             | Used in `src/api/runs.py` for trace forwarding   |
| `OTLP_FORWARDER_HEADERS`      | object  | null                  | OTLP forwarder headers                 | Used in `src/api/runs.py` for trace forwarding   |

### Performance Settings

| Variable            | Type    | Default | Description                | Usage                                              |
| ------------------- | ------- | ------- | -------------------------- | -------------------------------------------------- |
| `MAX_TRACE_SIZE_MB` | integer | 10      | Maximum trace size in MB   | Used in `src/core/config.py` for trace size limits |
| `REQUEST_TIMEOUT`   | integer | 30      | Request timeout in seconds | Used in `src/core/config.py` for request handling  |

### Logging Configuration

| Variable     | Type   | Default | Description               | Usage                                                                    |
| ------------ | ------ | ------- | ------------------------- | ------------------------------------------------------------------------ |
| `LOG_LEVEL`  | string | "INFO"  | Logging level             | Used in `src/core/config.py` and `src/main.py` for logging configuration |
| `LOG_FORMAT` | string | "json"  | Log format (json or text) | Used in `src/core/config.py` for logging format                          |
| `LOG_FILE`   | string | null    | Log file path             | Used in `src/core/config.py` for file logging                            |

### WebSocket Configuration

| Variable                       | Type    | Default | Description                             | Usage                                                    |
| ------------------------------ | ------- | ------- | --------------------------------------- | -------------------------------------------------------- |
| `WEBSOCKET_ENABLED`            | boolean | true    | Enable WebSocket support                | Used in `src/core/config.py` for WebSocket configuration |
| `WEBSOCKET_MAX_CONNECTIONS`    | integer | 100     | Maximum WebSocket connections           | Used in `src/core/config.py` for WebSocket limits        |
| `WEBSOCKET_HEARTBEAT_INTERVAL` | integer | 30      | WebSocket heartbeat interval in seconds | Used in `src/core/config.py` for WebSocket health checks |

### LangSmith Compatibility

| Variable                   | Type    | Default   | Description                                  | Usage                                                   |
| -------------------------- | ------- | --------- | -------------------------------------------- | ------------------------------------------------------- |
| `LANGSMITH_ENDPOINT_BASE`  | string  | "/api/v1" | Base path for LangSmith-compatible endpoints | Used in `src/main.py` for API routing                   |
| `SUPPORT_LEGACY_ENDPOINTS` | boolean | true      | Support legacy LangChain endpoint formats    | Used in `src/core/config.py` for backward compatibility |

## Frontend Environment Variables

### API Configuration

| Variable            | Type   | Default                        | Description                                      | Usage                                                                       |
| ------------------- | ------ | ------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------------- |
| `VITE_API_BASE_URL` | string | "http://localhost:3001/api/v1" | Base URL for API calls (includes /api/v1 suffix) | Used in `frontend/src/config/environment.ts` for API endpoint configuration |

### Port Configuration

| Variable             | Type   | Default | Description          | Usage                                                                                                   |
| -------------------- | ------ | ------- | -------------------- | ------------------------------------------------------------------------------------------------------- |
| `VITE_BACKEND_PORT`  | string | "8000"  | Backend server port  | Used in `frontend/src/config/environment.ts` and `frontend/vite.config.ts` for proxy configuration      |
| `VITE_FRONTEND_PORT` | string | "3001"  | Frontend server port | Used in `frontend/src/config/environment.ts` and `frontend/vite.config.ts` for dev server configuration |

**Note**: These Vite variables should reference the external port mapping variables:

- `VITE_BACKEND_PORT` should reference `BACKEND_EXTERNAL_PORT`
- `VITE_FRONTEND_PORT` should reference the internal port (3000 for dev, 80 for prod)
- `FRONTEND_PORT` is used by Vite config to determine the internal port

### Host Configuration

| Variable            | Type   | Default     | Description         | Usage                                                                                              |
| ------------------- | ------ | ----------- | ------------------- | -------------------------------------------------------------------------------------------------- |
| `VITE_BACKEND_HOST` | string | "localhost" | Backend server host | Used in `frontend/src/config/environment.ts` and `frontend/vite.config.ts` for proxy configuration |

### WebSocket Configuration

| Variable | Type            | Default        | Description                                                      | Usage                                                                 |
| -------- | --------------- | -------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------- |
| _None_   | _Auto-inferred_ | _From API URL_ | WebSocket URL is automatically inferred from `VITE_API_BASE_URL` | Used in `frontend/src/hooks/useWebSocket.ts` for WebSocket connection |

### Development Configuration

| Variable | Type    | Default       | Description                                             | Usage                                                                       |
| -------- | ------- | ------------- | ------------------------------------------------------- | --------------------------------------------------------------------------- |
| `DEV`    | boolean | false         | Enable development features (automatically set by Vite) | Used in `frontend/src/config/environment.ts` for development mode detection |
| `MODE`   | string  | "development" | Build mode (automatically set by Vite)                  | Used in `frontend/src/config/environment.ts` for environment detection      |

## Test Environment Variables

### Test Configuration

| Variable              | Type    | Default                                                           | Description            | Usage                                                                               |
| --------------------- | ------- | ----------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------- |
| `TESTING`             | boolean | false                                                             | Test environment flag  | Used in `tests/conftest.py` and `src/core/config.py` for test environment detection |
| `PYTEST_CURRENT_TEST` | string  | null                                                              | Pytest test identifier | Used in `src/core/config.py` for test environment detection                         |
| `TEST_DATABASE_TYPE`  | string  | "sqlite"                                                          | Test database type     | Used in `tests/conftest.py` for test database configuration                         |
| `TEST_DATABASE_URL`   | string  | "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db" | Test database URL      | Used in `tests/conftest.py` for test database configuration                         |

## External Service Integration

### LangSmith/LangChain Integration

| Variable               | Type    | Default | Description              | Usage                                                     |
| ---------------------- | ------- | ------- | ------------------------ | --------------------------------------------------------- |
| `LANGCHAIN_TRACING_V2` | boolean | false   | Enable LangChain tracing | Used in various test files for LangChain integration      |
| `LANGCHAIN_ENDPOINT`   | string  | null    | LangChain endpoint URL   | Used in test files for LangChain configuration            |
| `LANGCHAIN_API_KEY`    | string  | null    | LangChain API key        | Used in test files for LangChain authentication           |
| `LANGCHAIN_PROJECT`    | string  | null    | LangChain project name   | Used in test files for LangChain project configuration    |
| `LANGSMITH_TRACING`    | boolean | false   | Enable LangSmith tracing | Used in example files for LangSmith integration           |
| `LANGSMITH_ENDPOINT`   | string  | null    | LangSmith endpoint URL   | Used in example files for LangSmith configuration         |
| `LANGSMITH_API_KEY`    | string  | null    | LangSmith API key        | Used in example files for LangSmith authentication        |
| `LANGSMITH_PROJECT`    | string  | null    | LangSmith project name   | Used in example files for LangSmith project configuration |

### Ollama Integration

| Variable      | Type   | Default                  | Description        | Usage                                        |
| ------------- | ------ | ------------------------ | ------------------ | -------------------------------------------- |
| `OLLAMA_HOST` | string | "http://localhost:11434" | Ollama server host | Used in example files for Ollama integration |

### OpenAI Integration

| Variable            | Type   | Default      | Description         | Usage                                                |
| ------------------- | ------ | ------------ | ------------------- | ---------------------------------------------------- |
| `OPENAI_API_KEY`    | string | null         | OpenAI API key      | Used in example files for OpenAI integration         |
| `OPENAI_API_BASE`   | string | null         | OpenAI API base URL | Used in example files for OpenAI configuration       |
| `OPENAI_MODEL_NAME` | string | "qwen2.5:7b" | OpenAI model name   | Used in example files for OpenAI model configuration |

## Docker Configuration

### PostgreSQL Docker Settings

| Variable            | Type    | Default             | Description                         | Usage                                 |
| ------------------- | ------- | ------------------- | ----------------------------------- | ------------------------------------- |
| `POSTGRES_DB`       | string  | "agentspy"          | PostgreSQL database name for Docker | Used in Docker Compose configurations |
| `POSTGRES_USER`     | string  | "agentspy_user"     | PostgreSQL username for Docker      | Used in Docker Compose configurations |
| `POSTGRES_PASSWORD` | string  | "agentspy_password" | PostgreSQL password for Docker      | Used in Docker Compose configurations |
| `POSTGRES_PORT`     | integer | 5432                | PostgreSQL port for Docker          | Used in Docker Compose configurations |

### Development Docker Settings

| Variable                 | Type    | Default | Description                  | Usage                                     |
| ------------------------ | ------- | ------- | ---------------------------- | ----------------------------------------- |
| `BACKEND_EXTERNAL_PORT`  | integer | 8001    | Backend external port (dev)  | Used in development Docker configurations |
| `FRONTEND_EXTERNAL_PORT` | integer | 3000    | Frontend external port (dev) | Used in development Docker configurations |

**Note**: Internal ports are fixed (backend: 8000, frontend: 3000 for dev, 80 for prod)

## Redundancies and Overlaps

### 1. **Dual Naming Conventions**

**Issue**: The project supports both old and new naming conventions for the same configuration values.

**Redundant Variables**:

- `HOST` ↔ `BACKEND_HOST`
- `PORT` ↔ `BACKEND_PORT`
- `DATABASE_HOST` ↔ `DB_HOST`
- `DATABASE_PORT` ↔ `DB_PORT`
- `DATABASE_NAME` ↔ `DB_NAME`
- `DATABASE_USER` ↔ `DB_USER`
- `DATABASE_PASSWORD` ↔ `DB_PASSWORD`
- `OTLP_GRPC_HOST` ↔ `BACKEND_OTLP_GRPC_HOST`
- `OTLP_GRPC_PORT` ↔ `BACKEND_OTLP_GRPC_PORT`

**Impact**:

- Confusion for developers about which naming convention to use
- Potential for conflicting values if both are set
- Increased complexity in configuration management

### 2. **Port Configuration Overlaps**

**Issue**: Multiple port-related variables that could conflict:

- `BACKEND_PORT` (backend config)
- `VITE_BACKEND_PORT` (frontend config)
- `BACKEND_DEV_PORT` (Docker dev config)
- `FRONTEND_PORT` (backend config)
- `VITE_FRONTEND_PORT` (frontend config)
- `FRONTEND_DEV_PORT` (Docker dev config)

**Impact**: Risk of misconfiguration between development and production environments.

### 3. **Database URL vs Component Configuration**

**Issue**: Both `DATABASE_URL` and individual database component variables can be used:

- `DATABASE_URL` (complete connection string)
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, etc. (individual components)

**Impact**: Potential for conflicting configurations if both are set.

### 4. **WebSocket URL Configuration**

**Issue**: ~~Multiple ways to configure WebSocket URL~~ **RESOLVED**

- ~~`API_WS_URL` (backend config)~~ **REMOVED**
- ~~`VITE_WS_URL` (frontend config)~~ **REMOVED**
- ~~Hardcoded fallback: `ws://localhost:8000/ws`~~ **REMOVED**

**Solution**: WebSocket URL is now automatically inferred from `VITE_API_BASE_URL` by converting HTTP/HTTPS to WS/WSS and appending `/ws`.

**Impact**: ✅ Simplified configuration with single source of truth.

### 5. **API Base URL Redundancy**

**Issue**: Similar variables for API configuration:

- `API_URL_BASE` (backend config)
- `VITE_API_BASE_URL` (frontend config)
- `API_PREFIX` (backend routing)

**Impact**: Potential for misalignment between frontend and backend API endpoints.

## Security Concerns

### 1. **Sensitive Data in Environment Variables**

**High Risk**:

- `DATABASE_PASSWORD` / `DB_PASSWORD` - Database credentials
- `API_KEYS` - Authentication keys
- `LANGCHAIN_API_KEY` / `LANGSMITH_API_KEY` - External service credentials
- `OPENAI_API_KEY` - External service credentials

**Concerns**:

- Passwords stored in plain text
- API keys exposed in environment
- No encryption for sensitive values
- Risk of credential leakage in logs

### 2. **Overly Permissive Defaults**

**Issues**:

- `CORS_ORIGINS=["*"]` - Allows all origins in production
- `REQUIRE_AUTH=false` - No authentication by default
- `DEBUG=false` but debug information still available

### 3. **Network Security**

**Issues**:

- `HOST="0.0.0.0"` - Binds to all interfaces by default
- No TLS/SSL configuration for production
- WebSocket connections without encryption

### 4. **Information Disclosure**

**Issues**:

- Detailed error messages in production (`DEBUG=false` but still shows error details)
- Database connection strings logged
- API endpoints exposed without rate limiting

## Recommendations

### 1. **Standardize Naming Convention**

**Action**: Choose one naming convention and deprecate the other.

**Recommendation**: Use the new convention (`BACKEND_*`, `DB_*`, etc.) and add deprecation warnings for old variables.

```python
# In config.py
import warnings

def get_database_host():
    if 'DATABASE_HOST' in os.environ:
        warnings.warn("DATABASE_HOST is deprecated, use DB_HOST instead", DeprecationWarning)
        return os.environ['DATABASE_HOST']
    return os.environ.get('DB_HOST', 'localhost')
```

### 2. **Implement Configuration Validation**

**Action**: Add validation to prevent conflicting configurations.

```python
def validate_config():
    if 'DATABASE_URL' in os.environ and any(k in os.environ for k in ['DB_HOST', 'DB_PORT', 'DB_NAME']):
        raise ValueError("Cannot use both DATABASE_URL and individual database components")
```

### 3. **Enhance Security**

**Actions**:

- Implement secrets management (e.g., HashiCorp Vault, AWS Secrets Manager)
- Add encryption for sensitive environment variables
- Implement proper CORS configuration for production
- Add rate limiting for API endpoints
- Enable authentication by default in production

### 4. **Simplify Configuration**

**Actions**:

- Consolidate port configuration into a single source of truth
- Create environment-specific configuration files
- Implement configuration inheritance (base → environment → local)
- Add configuration validation and documentation

### 5. **Improve Documentation**

**Actions**:

- Add required vs optional variable indicators
- Document environment-specific configurations
- Add security best practices
- Create configuration templates for different deployment scenarios

### 6. **Add Configuration Testing**

**Actions**:

- Create tests for configuration validation
- Add integration tests for different environment setups
- Implement configuration health checks
- Add automated configuration validation in CI/CD

## Configuration Priority

The current configuration loading priority is:

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

**Recommendation**: Consider implementing a more structured approach:

1. Base configuration (defaults)
2. Environment-specific configuration
3. Local development overrides
4. Runtime environment variables (highest priority)

## Environment-Specific Configurations

### Development

- Enable debug mode
- Use SQLite database
- Allow all CORS origins
- Disable authentication
- Enable detailed logging

### Production

- Disable debug mode
- Use PostgreSQL database
- Restrict CORS origins
- Enable authentication
- Use structured logging
- Enable SSL/TLS
- Implement rate limiting

### Testing

- Use in-memory SQLite
- Disable external services
- Use test-specific ports
- Enable test mode flags

## Conclusion

While the current environment variable system provides flexibility, it has several areas for improvement:

1. **Standardization**: Choose and enforce a single naming convention
2. **Security**: Implement proper secrets management and security defaults
3. **Validation**: Add configuration validation to prevent conflicts
4. **Documentation**: Improve documentation and provide clear examples
5. **Testing**: Add comprehensive configuration testing

These improvements will make the system more maintainable, secure, and user-friendly.
