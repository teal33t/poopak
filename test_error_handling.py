#!/usr/bin/env python3
"""
Simple test script to verify error handling implementation.

This script tests that:
1. Error handlers are properly registered
2. Custom exceptions are handled correctly
3. Error context logging works
4. Error tracking is initialized
"""

import sys
import os

# Add application to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from application.web import create_app
from application.config import Settings
from application.utils.exceptions import (
    DocumentNotFoundError,
    ValidationError,
    DatabaseConnectionError,
    CrawlerError,
    DetectionError,
)


def test_error_handlers():
    """Test that error handlers are properly registered."""
    print("Testing error handler registration...")
    
    # Create test app
    test_settings = Settings()
    test_settings.ERROR_TRACKING_ENABLED = False  # Disable for testing
    app = create_app(test_settings)
    
    # Check error handlers are registered
    error_handlers = app.error_handler_spec.get(None, {})
    
    # Check HTTP error handlers
    assert 400 in error_handlers, "400 error handler not registered"
    assert 401 in error_handlers, "401 error handler not registered"
    assert 403 in error_handlers, "403 error handler not registered"
    assert 404 in error_handlers, "404 error handler not registered"
    assert 500 in error_handlers, "500 error handler not registered"
    
    # Check custom exception handlers
    exception_handlers = error_handlers.get(None, {})
    assert DocumentNotFoundError in exception_handlers, "DocumentNotFoundError handler not registered"
    assert ValidationError in exception_handlers, "ValidationError handler not registered"
    assert DatabaseConnectionError in exception_handlers, "DatabaseConnectionError handler not registered"
    assert CrawlerError in exception_handlers, "CrawlerError handler not registered"
    assert DetectionError in exception_handlers, "DetectionError handler not registered"
    
    print("✓ All error handlers registered successfully")
    return True


def test_error_context():
    """Test error context creation."""
    print("\nTesting error context...")
    
    from application.web.errors import ErrorContext
    
    # Create test error
    test_error = ValueError("Test error")
    
    # Create error context
    context = ErrorContext(
        error=test_error,
        endpoint="test.endpoint",
        user_id="test_user",
        additional_data={"key": "value"}
    )
    
    # Verify context
    assert context.error_type == "ValueError"
    assert context.error_message == "Test error"
    assert context.endpoint == "test.endpoint"
    assert context.user_id == "test_user"
    assert context.additional_data["key"] == "value"
    
    # Test to_dict
    context_dict = context.to_dict()
    assert "error_type" in context_dict
    assert "error_message" in context_dict
    assert "endpoint" in context_dict
    
    print("✓ Error context works correctly")
    return True


def test_error_tracker():
    """Test error tracker initialization."""
    print("\nTesting error tracker...")
    
    from application.web.error_tracking import ErrorTracker
    
    # Create tracker
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
    
    print("✓ Error tracker works correctly")
    return True


def test_app_initialization():
    """Test that app initializes with error tracking."""
    print("\nTesting app initialization with error tracking...")
    
    test_settings = Settings()
    test_settings.ERROR_TRACKING_ENABLED = False
    app = create_app(test_settings)
    
    # Check error tracker is attached
    assert hasattr(app, "error_tracker"), "Error tracker not attached to app"
    
    print("✓ App initializes with error tracking")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Error Handling Implementation Tests")
    print("=" * 60)
    
    tests = [
        test_error_handlers,
        test_error_context,
        test_error_tracker,
        test_app_initialization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed: {test.__name__}")
            print(f"  Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
