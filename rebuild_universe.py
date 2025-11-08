#!/usr/bin/env python3
"""
Rebuild the risk_universes.json file with real asset classifications
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from risk_management.asset_classification import AssetClassifier


def main():
    print("Rebuilding risk universes with real market data...")
    
    # Create a new AssetClassifier instance
    classifier = AssetClassifier()
    
    # Force update the universes (this will classify all assets and save to risk_universes.json)
    classifier.update_universes()
    
    # Print the results
    print(f"Low risk assets: {len(classifier.universes['low'])}")
    print(f"Medium risk assets: {len(classifier.universes['medium'])}")
    print(f"High risk assets: {len(classifier.universes['high'])}")
    
    print("\nSample low risk assets:", classifier.universes['low'][:10])
    print("Sample medium risk assets:", classifier.universes['medium'][:10])
    print("Sample high risk assets:", classifier.universes['high'][:10])
    
    print("\nRisk universes have been rebuilt and saved to risk_universes.json")


if __name__ == "__main__":
    main()