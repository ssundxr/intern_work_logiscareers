# Clean Architecture Implementation

## Why main.py is at Project Root (Not in api/)

### The Problem with api/app.py

When the application factory lives inside `api/`, it creates several architectural issues:

1. **Inverted Dependencies**: The API layer appears to "own" the application lifecycle
2. **Unclear Boundaries**: Composition logic is conflated with the delivery mechanism
3. **Operational Friction**: Non-standard deployment patterns (`uvicorn api.app:app`)
4. **Limited Testability**: Tests must import from a delivery layer
5. **Reduced Reusability**: Cannot easily add CLI, workers, or other interfaces

### The Solution: Composition Root at Project Root

```
Project Structure:
├── main.py              ← Composition Root (app factory, handlers, lifecycle)
├── api/
│   └── routes/          ← Delivery Layer (ONLY routes)
│       ├── cv.py
│       ├── evaluation.py
│       └── health.py
├── application/         ← Application Services
├── core/                ← Domain Logic
└── ml/                  ← Infrastructure
```

### Responsibilities

#### main.py (Composition Root)
- Creates FastAPI app instance
- Registers exception handlers
- Attaches lifecycle hooks (startup/shutdown)
- Configures middleware and CORS
- Registers routes from api/ layer
- **Does NOT belong to any single layer** - sits above all layers

#### api/routes/ (Delivery Layer)
- HTTP request handlers ONLY
- Request/response serialization
- Delegates to application services
- **NO app factory, NO handlers, NO lifecycle**

### Benefits

1. **Clear Separation of Concerns**
   - Composition is separate from delivery
   - Each layer has a single, well-defined responsibility

2. **Standard Deployment Patterns**
   ```bash
   uvicorn main:app                    # Standard pattern
   gunicorn main:app -k uvicorn.workers.UvicornWorker
   ```

3. **Testability**
   ```python
   from main import create_app  # Import from composition root
   
   def test_app():
       app = create_app()
       # Test with different configurations
   ```

4. **Future Extensibility**
   ```python
   # CLI can reuse composition root
   from main import create_app
   
   # Worker can reuse composition root
   from main import create_app
   
   # gRPC server can reuse composition root
   # All share the same composition pattern
   ```

5. **Correct Dependency Direction**
   ```
   main.py (composition root)
      ↓
   api/routes/ (delivery)
      ↓
   application/ (services)
      ↓
   core/ (domain)
      ↓
   ml/ (infrastructure)
   ```

## Industry Standard

This pattern is followed across frameworks and languages:

- **Django**: `manage.py` at project root
- **Flask**: `app.py` or `wsgi.py` at project root
- **Spring Boot**: `Application.java` at root package
- **ASP.NET Core**: `Program.cs` at project root
- **Node.js/Express**: `server.js` or `app.js` at project root

The composition root is **always at the project root**, never inside a delivery mechanism folder.

## Key Takeaway

**The api/ folder contains ONLY routes** - it's a delivery mechanism, not the application owner.

**The composition root (main.py) sits above all layers** - it wires them together but doesn't belong to any single layer.

This is not a stylistic choice - it's an architectural principle that improves:
- Separation of concerns
- Operational clarity
- Testability
- Long-term maintainability
