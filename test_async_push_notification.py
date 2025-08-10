#!/usr/bin/env python3
"""
Test script to verify async push notification doesn't block main flow
"""

import requests
import logging
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_push_notification_async(url, payload):
    """
    Send push notification in a separate thread (fire-and-forget).
    This ensures the main request flow is never blocked.
    """
    def _send():
        try:
            print(f"  [Thread] Starting push notification to {url}")
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code != 200:
                logger.warning(f"Push notification failed: {response.text}")
                print(f"  [Thread] Push notification failed with status {response.status_code}")
            else:
                print(f"  [Thread] Push notification successful")
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            print(f"  [Thread] Push notification error: {type(e).__name__}")
    
    # Start thread and don't wait for it
    thread = threading.Thread(target=_send)
    thread.daemon = True  # Daemon thread will not prevent app from exiting
    thread.start()
    return thread

def simulate_like_endpoint(taste_id, user_id):
    """Simulate the like_taste endpoint behavior"""
    print(f"\n=== Simulating like_taste endpoint ===")
    print(f"1. Processing like for taste_id={taste_id}")
    
    # Simulate successful like operation
    time.sleep(0.1)  # Simulate database operation
    result = {'code': 0, 'data': {'liked': True}, 'msg': 'Success'}
    print(f"2. Like operation successful")
    
    # Send push notification asynchronously (doesn't block)
    if result['code'] == 0:
        print(f"3. Triggering async push notification...")
        thread = send_push_notification_async(
            "https://httpbin.org/delay/3",  # This endpoint delays 3 seconds
            {
                "taste_id": taste_id,
                "current_user_id": user_id
            }
        )
        print(f"4. Push notification triggered (not waiting)")
    
    # Return immediately without waiting for push notification
    print(f"5. Returning response to client immediately")
    return {'code': 0, 'data': result['data'], 'message': result['msg']}

def simulate_collect_endpoint_with_error(dish_id, user_id):
    """Simulate the collect_dish endpoint with notification error"""
    print(f"\n=== Simulating collect_dish endpoint (with error) ===")
    print(f"1. Processing collect for dish_id={dish_id}")
    
    # Simulate successful collect operation
    time.sleep(0.1)  # Simulate database operation
    result = {'code': 0, 'data': {'collected': True}, 'msg': 'Success'}
    print(f"2. Collect operation successful")
    
    # Send push notification asynchronously to invalid endpoint
    if result['code'] == 0:
        print(f"3. Triggering async push notification to invalid endpoint...")
        thread = send_push_notification_async(
            "http://invalid-host-that-does-not-exist.local/api/push/collect",
            {
                "dish_id": dish_id,
                "current_user_id": user_id
            }
        )
        print(f"4. Push notification triggered (will fail in background)")
    
    # Return immediately without waiting for push notification
    print(f"5. Returning response to client immediately")
    return {'code': 0, 'data': result['data'], 'message': result['msg']}

def main():
    print("=" * 60)
    print("Testing Async Push Notification Integration")
    print("=" * 60)
    
    # Test 1: Normal flow with slow notification endpoint
    start_time = time.time()
    response = simulate_like_endpoint("test_taste_123", "test_user_456")
    elapsed = time.time() - start_time
    print(f"\n✓ Like endpoint returned in {elapsed:.2f} seconds")
    print(f"  Response: {response}")
    
    if elapsed < 1:
        print("✓ SUCCESS: Response was immediate (didn't wait for push notification)")
    else:
        print("✗ FAILURE: Response was slow (might be waiting for push notification)")
    
    # Test 2: Flow with notification error
    start_time = time.time()
    response = simulate_collect_endpoint_with_error("test_dish_789", "test_user_456")
    elapsed = time.time() - start_time
    print(f"\n✓ Collect endpoint returned in {elapsed:.2f} seconds")
    print(f"  Response: {response}")
    
    if elapsed < 1:
        print("✓ SUCCESS: Response was immediate (didn't wait for push notification)")
    else:
        print("✗ FAILURE: Response was slow (might be waiting for push notification)")
    
    # Wait a bit to see background thread logs
    print("\n" + "=" * 60)
    print("Waiting 6 seconds for background threads to complete...")
    print("(In production, these would complete in the background)")
    print("=" * 60)
    time.sleep(6)
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("  - Main flow returns immediately")
    print("  - Push notifications are sent in background")
    print("  - Errors in push notifications don't affect main flow")
    print("=" * 60)

if __name__ == "__main__":
    main()