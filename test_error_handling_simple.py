#!/usr/bin/env python3
"""
Simple test script to verify error handling modules can be imported.
"""

import sys
import os

# Add application to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing error handling implementation...")
print("=" * 60)

# Test 1: Import error handling modules
print("\n1. Testing module imports...")
try:
    from application.web.errors import (
        ErrorContext,
        log_error_with_context,
        get_error_response,
        register_error_handlers,
    )
    print("   ✓ application.web.errors imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import application.web.errors: {e}")
    sys.exit(1)

try:
    from application.web.error_tracking import ErrorTracker, init_error_tracking
    print("   ✓ application.web.error_tracking imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import application.web.error_tracking: {e}")
    sys.exit(1)

# Test 2: Test ErrorContext
print("\n2. Testing ErrorContext class...")
try:
    test_error = ValueError("Test error")
    context = ErrorContext(
        error=test_error,
        endpoint="test.endpoint",
        user_id="test_user",
        additional_data={"key": "value"}
    )
    
    assert context.error_type == "ValueError"
    assert context.error_message == "Test error"
    assert context.endpoint == "test.endpoint"
    assert context.user_id == "test_user"
    
    context_dict = context.to_dict()
    assert "error_type" in context_dict
    assert "error_message" in context_dict
    
    print("   ✓ ErrorContext works correctly")
except Exception as e:
    print(f"   ✗ ErrorContext test failed: {e}")
    sys.exit(1)

# Test 3: Test ErrorTracker
print("\n3. Testing ErrorTracker class...")
try:
    tracker = ErrorTracker(enabled=False)
    
    # Test capture (should not fail even when disabled)
    test_error = Exception("Test error")
    tracker.capture_exception(test_error, context={"test": "data"})
    
    # Test custom handler
    handler_called = []
    
    def custom_handler(error, context, level):
        handler_called.append(True)
    
    tracker.add_custom_handler(custom_handler)
    tracker.enabled = True
    tracker.capture_exception(test_error)
    
    assert len(handler_called) > 0, "Custom handler not called"
    
    print("   ✓ ErrorTracker works correctly")
except Exception as e:
    print(f"   ✗ ErrorTracker test failed: {e}")
    sys.exit(1)

# Test 4: Check configuration
print("\n4. Testing configuration...")
try:
    from application.config import Settings
    
    settings = Settings()
    assert hasattr(settings, "ERROR_TRACKING_ENABLED")
    assert hasattr(settings, "SENTRY_DSN")
    assert hasattr(settings, "ENVIRONMENT")
    
    print("   ✓ Configuration includes error tracking settings")
except Exception as e:
    print(f"   ✗ Configuration test failed: {e}")
    sys.exit(1)

# Test 5: Check custom exceptions
print("\n5. Testing custom exceptions...")
try:
    from application.utils.exceptions import (
        ApplicationError,
        DocumentNotFoundError,
        ValidationError,
        DatabaseConnectionError,
        CrawlerError,
        DetectionError,
    )
    
    # Test exception hierarchy
    assert issubclass(DocumentNotFoundError, ApplicationError)
    assert issubclass(ValidationError, ApplicationError)
    assert issubclass(DatabaseConnectionError, ApplicationError)
    
    print("   ✓ Custom exceptions are properly defined")
except Exception as e:
    print(f"   ✗ Custom exceptions test failed: {e}")
    sys.exit(1)

# Test 6: Check templates exist
print("\n6. Testing error templates...")
try:
    import os
    
    template_dir = "application/web/templates"
    error_templates = [
        "error.html",
        "errors/404.html",
        "errors/403.html",
        "errors/500.html",
    ]
    
    for template in error_templates:
        template_path = os.path.join(template_dir, template)
        assert os.path.exists(template_path), f"Template {template} not found"
    
    print("   ✓ All error templates exist")
except Exception as e:
    print(f"   ✗ Template test failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed! ✓")
print("=" * 60)
print("\nError handling implementation is complete:")
print("  • Comprehensive error handlers registered")
print("  • Custom error pages created")
print("  • Error logging with context implemented")
print("  • Production error tracking ready")
print("  • Configuration updated")
