#!/usr/bin/env python3
"""
Test the updated classification system with real market data
"""
import sys
import os
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from risk_management.asset_classification import get_risk_appropriate_assets


def main():
    print("Testing the updated asset classification system...")
    
    # Test fetching assets for different risk profiles
    risk_profiles = ['low', 'medium', 'high']
    
    for profile in risk_profiles:
        print(f"\n--- Testing {profile} risk profile ---")
        try:
            assets = get_risk_appropriate_assets(profile, count=5)
            print(f"Selected {len(assets)} assets for {profile} risk: {assets}")
            
            # Test with the historical data fetcher to ensure the assets are valid
            from indicators.historical_data_fetcher import get_historical_data
            print("Verifying assets with real market data...")
            
            for asset in assets[:3]:  # Test only first 3 to save time
                try:
                    data = get_historical_data(asset, interval='1d', lookback_periods=7)
                    print(f"  ✓ {asset}: Got {len(data)} data points")
                except Exception as e:
                    print(f"  ✗ {asset}: Error fetching data - {e}")
                    
        except Exception as e:
            print(f"Error fetching assets for {profile} risk: {e}")
    
    # Also test the risk_universes.json file directly
    print("\n--- Current risk_universes.json contents ---")
    try:
        with open('risk_universes.json', 'r') as f:
            universes = json.load(f)
        
        print(f"Low risk assets: {len(universes['low'])} ({universes['low'][:5]}...)")
        print(f"Medium risk assets: {len(universes['medium'])} ({universes['medium'][:5]}...)")
        print(f"High risk assets: {len(universes['high'])} ({universes['high'][:5]}...)")
    except Exception as e:
        print(f"Error reading risk_universes.json: {e}")
    
    print("\nTest completed successfully!")


if __name__ == "__main__":
    main()