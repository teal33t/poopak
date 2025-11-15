# Error Handling Documentation

## Overview

The application now includes comprehensive error handling with proper HTTP status codes, custom error pages, contextual logging, and production error tracking capabilities.

## Features

### 1. Comprehensive Error Handlers

The application handles the following error types:

- **HTTP Errors**: 400, 401, 403, 404, 500
- **CSRF Errors**: Session expiration and token validation
- **Application Errors**:
  - `DocumentNotFoundError`: When documents are not found
  - `ValidationError`: Input validation failures
  - `DatabaseConnectionError`: Database connectivity issues
  - `CrawlerError`: Crawling operation failures
  - `DetectionError`: EXIF/subject detection failures
  - Generic `ApplicationError`: Catch-all for custom errors
- **Unexpected Errors**: Catch-all for any unhandled exceptions

### 2. Custom Error Pages

Custom error templates are provided for common errors:

- `errors/404.html`: Page not found
- `errors/403.html`: Access forbidden
- `errors/500.html`: Internal server error
- `error.html`: Generic error template

Each template includes:
- Clear error messaging
- Navigation options (home, back)
- Helpful suggestions for users
- Consistent styling with the application

### 3. Error Logging with Context

The `ErrorContext` class captures comprehensive error information:

```python
from application.web.errors import log_error_with_context

# Log error with full context
log_error_with_context(
    error=exception,
    endpoint="dashboard.hs_view",
    user_id=current_user.id,
    additional_data={"document_id": doc_id}
)
```

Captured context includes:
- Error type and message
- Request URL and method
- User agent and IP address
- Endpoint and user ID
- Custom additional data
- Full stack trace

### 4. Production Error Tracking

The `ErrorTracker` class provides integration with external monitoring services:

#### Sentry Integration

To enable Sentry error tracking, set the following environment variables:

```bash
ERROR_TRACKING_ENABLED=True
SENTRY_DSN=your_sentry_dsn_here
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production
APP_VERSION=1.0.0
```

#### Custom Error Handlers

You can add custom error handlers:

```python
from flask import current_app

def my_error_handler(error, context, level):
    # Custom error handling logic
    print(f"Error: {error}, Context: {context}")

# Add handler
current_app.error_tracker.add_custom_handler(my_error_handler)
```

#### Manual Error Tracking

Track errors manually in your code:

```python
from flask import current_app

try:
    # Your code here
    pass
except Exception as e:
    current_app.error_tracker.capture_exception(
        e,
        context={"custom_data": "value"},
        level="error"
    )
```

## Usage in Views

### Proper Error Handling Pattern

```python
from flask import flash, redirect, url_for
from application.utils.exceptions import DocumentNotFoundError, DatabaseConnectionError

@blueprint.route('/document/<document_id>')
def view_document(document_id: str):
    try:
        document = document_service.get_document(document_id)
        return render_template('document.html', document=document)
    
    except DocumentNotFoundError:
        flash("Document not found", "error")
        return redirect(url_for('dashboard.index')), 404
    
    except DatabaseConnectionError as e:
        logger.error(f"Database error: {str(e)}")
        flash("A database error occurred", "error")
        return redirect(url_for('dashboard.index')), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        flash("An unexpected error occurred", "error")
        return redirect(url_for('dashboard.index')), 500
```

### Error Response Helper

Use the `get_error_response` helper for consistent error responses:

```python
from application.web.errors import get_error_response

try:
    # Your code
    pass
except CustomError as e:
    return get_error_response(
        e,
        status_code=400,
        title="Custom Error",
        description="A custom error occurred"
    )
```

## Configuration

### Environment Variables

```bash
# Error Tracking
ERROR_TRACKING_ENABLED=False  # Enable in production
SENTRY_DSN=                   # Your Sentry DSN
SENTRY_TRACES_SAMPLE_RATE=0.1 # Sample rate for performance monitoring
ENVIRONMENT=development       # Environment name
APP_VERSION=1.0.0            # Application version
```

### Flask Configuration

The error handling system is automatically initialized in `create_app()`:

```python
app = create_app()
# Error handlers are registered
# Error tracking is initialized
```

## Best Practices

1. **Use Specific Exceptions**: Raise specific exception types rather than generic `Exception`
2. **Log with Context**: Always include relevant context when logging errors
3. **User-Friendly Messages**: Show generic messages to users, log detailed info server-side
4. **Proper Status Codes**: Return appropriate HTTP status codes with error responses
5. **Flash Messages**: Use flash messages for user feedback before redirects
6. **Track Critical Errors**: Ensure critical errors are tracked in production
7. **Don't Expose Internals**: Never expose stack traces or internal details to users

## Testing Error Handlers

You can test error handlers in development:

```python
# Test 404 handler
@app.route('/test-404')
def test_404():
    abort(404)

# Test 500 handler
@app.route('/test-500')
def test_500():
    raise Exception("Test error")

# Test custom exception
@app.route('/test-not-found')
def test_not_found():
    raise DocumentNotFoundError("Test document not found")
```

## Monitoring and Alerts

When error tracking is enabled:

1. All 500 errors are automatically tracked
2. Database connection errors are tracked
3. Unexpected exceptions are tracked with full context
4. You can set up alerts in your monitoring service (e.g., Sentry)

## Troubleshooting

### Error Tracking Not Working

1. Check `ERROR_TRACKING_ENABLED` is set to `True`
2. Verify `SENTRY_DSN` is correctly configured
3. Ensure `sentry-sdk` is installed: `pip install sentry-sdk`
4. Check application logs for initialization errors

### Custom Error Pages Not Showing

1. Verify templates exist in `application/web/templates/errors/`
2. Check Flask is in production mode (not debug mode)
3. Ensure error handlers are registered in `create_app()`

### Logs Missing Context

1. Verify logging is properly configured
2. Use `log_error_with_context()` instead of basic logging
3. Check log file permissions and paths
