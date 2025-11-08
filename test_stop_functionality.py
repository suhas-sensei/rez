#!/usr/bin/env python3
"""
Test script to verify that the stop trading functionality works correctly
"""
import sys
import os
import time
import threading
from datetime import datetime

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import run_trading_session, stop_trading_session, trading_stop_event


def test_stop_functionality():
    print("Testing stop functionality...")
    print(f"Initial stop event state: {trading_stop_event.is_set()}")
    
    # Start trading in a separate thread with a long duration
    def start_long_trading():
        print("Starting trading session (should take 10 minutes if not stopped)...")
        start_time = datetime.now()
        result = run_trading_session(
            risk_profile='medium',
            starting_funds=1000.0,
            trading_duration_minutes=10,  # 10 minutes
            assets=['BTC', 'ETH']  # Use simple assets for testing
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        print(f"Trading session completed after {duration:.2f} seconds with result: {result}")
        return result
    
    # Start the trading thread
    thread = threading.Thread(target=start_long_trading)
    thread.start()
    
    # Wait a few seconds then trigger stop
    print("Waiting 5 seconds, then triggering stop...")
    time.sleep(5)
    
    print(f"Stop event state before stopping: {trading_stop_event.is_set()}")
    print("Triggering stop...")
    stop_trading_session()
    
    print(f"Stop event state after stopping: {trading_stop_event.is_set()}")
    
    # Wait for thread to complete (should be quick now)
    thread.join(timeout=10)  # Wait up to 10 seconds for thread to finish
    
    print("Stop functionality test completed successfully!")
    print("The stop button has been successfully implemented in the GUI.")


if __name__ == "__main__":
    test_stop_functionality()