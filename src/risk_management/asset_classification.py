"""
Asset Classification and Universe Management Module
Implements risk-based asset classification and dynamic universe selection
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.historical_data_fetcher import get_historical_data
from config_loader import load_config


class AssetClassifier:
    """
    Classifies assets based on risk metrics and maintains risk-based universes
    """
    
    def __init__(self):
        self.config = load_config()
        self.universes = {
            'low': [],
            'medium': [],
            'high': []
        }
        # Load or create universes
        self._load_universes()
    
    def calculate_risk_score(self, asset: str, lookback_days: int = 30) -> float:
        """
        Calculate risk score for an asset based on multiple factors
        Returns score between 0.0 (low risk) and 1.0 (high risk)
        """
        try:
            # Get historical data for the asset
            df = get_historical_data(asset, interval='1d', lookback_periods=lookback_days)
            
            # Calculate volatility (standard deviation of returns)
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() if len(returns) > 0 else 0.05  # Default to 5% if no data
            
            # Calculate ATR-based volatility
            high_low_diff = (df['high'] - df['low']) / df['close']
            avg_atr = high_low_diff.mean() if len(high_low_diff) > 0 else 0.03
            
            # Get average volume
            avg_volume = df['volume'].mean() if len(df['volume']) > 0 else 1000000  # Default to $1M
            
            # Calculate price volatility relative to volume
            volume_adjusted_volatility = volatility / max(1, avg_volume / 1000000)
            
            # Risk scoring components (weighted)
            # Higher volatility = higher risk
            volatility_score = min(1.0, volatility * 20)  # Scale volatility appropriately
            
            # Lower volume = higher risk
            volume_score = max(0.0, 1.0 - min(1.0, avg_volume / 50000000))  # Normalize volume to risk
            
            # ATR score
            atr_score = min(1.0, avg_atr * 20)  # Scale ATR appropriately
            
            # Weighted risk score
            risk_score = (
                volatility_score * 0.4 + 
                volume_score * 0.3 + 
                atr_score * 0.3
            )
            
            # Bound the score between 0 and 1
            risk_score = max(0.0, min(1.0, risk_score))
            
            return risk_score
            
        except Exception as e:
            print(f"Error calculating risk score for {asset}: {e}")
            # Default to medium risk if calculation fails
            return 0.5
    
    def classify_asset(self, asset: str, lookback_days: int = 30) -> str:
        """
        Classify asset into risk category based on risk score
        Returns: 'low', 'medium', or 'high'
        """
        risk_score = self.calculate_risk_score(asset, lookback_days)
        
        if risk_score <= 0.3:
            return 'low'
        elif risk_score <= 0.7:
            return 'medium'
        else:
            return 'high'
    
    def build_universe(self, assets_list: list = None) -> dict:
        """
        Build risk-based universes from a list of assets
        """
        if assets_list is None:
            # Default crypto universe
            assets_list = [
                'BTC', 'ETH', 'SOL', 'AVAX', 'ADA', 'DOT', 'LINK', 'MATIC', 
                'UNI', 'LTC', 'BCH', 'ETC', 'XLM', 'TRX', 'DOGE', 'XRP', 
                'ATOM', 'NEAR', 'APT', 'ARB', 'PEPE', 'SHIB', 'POL', 'XMR', 
                'ALGO', 'XTZ', 'BCH', 'BSV', 'DGB', 'RVN', 'ZEC', 'ENJ', 
                'MANA', 'SAND', 'AAVE', 'CRV', 'COMP', 'MKR', 'YFI', 'SNX'
            ]
        
        universes = {
            'low': [],
            'medium': [],
            'high': []
        }
        
        for asset in assets_list:
            try:
                risk_category = self.classify_asset(asset)
                universes[risk_category].append(asset)
            except Exception as e:
                print(f"Error classifying asset {asset}: {e}")
                # Default to medium risk if classification fails
                universes['medium'].append(asset)
        
        return universes
    
    def update_universes(self, assets_list: list = None):
        """
        Update the risk-based universes
        """
        self.universes = self.build_universe(assets_list)
        self._save_universes()
    
    def get_assets_for_risk_profile(self, risk_profile: str) -> list:
        """
        Get assets appropriate for a specific risk profile
        """
        # Normalize risk profile
        normalized_risk = risk_profile.lower()
        
        # Return assets for the specified risk profile
        if normalized_risk in self.universes:
            return self.universes[normalized_risk]
        else:
            # Default to medium risk if invalid profile
            return self.universes['medium']
    
    def _save_universes(self):
        """
        Save universes to file for persistence
        """
        try:
            with open('risk_universes.json', 'w') as f:
                json.dump(self.universes, f)
        except Exception as e:
            print(f"Error saving universes: {e}")
    
    def _load_universes(self):
        """
        Load universes from file if they exist
        """
        try:
            if os.path.exists('risk_universes.json'):
                with open('risk_universes.json', 'r') as f:
                    self.universes = json.load(f)
            else:
                # Build default universes if file doesn't exist
                self.update_universes()
        except Exception as e:
            print(f"Error loading universes: {e}")
            # Build default universes
            self.update_universes()


class DynamicAssetSelector:
    """
    Selects assets from universes with additional dynamic filtering
    """
    
    def __init__(self):
        self.asset_classifier = AssetClassifier()
    
    def select_assets(
        self, 
        risk_profile: str, 
        count: int = 6, 
        exclude_assets: list = None
    ) -> list:
        """
        Select assets from the appropriate universe with dynamic filtering and diversity
        """
        if exclude_assets is None:
            exclude_assets = []
        
        # Get base universe for risk profile
        base_assets = self.asset_classifier.get_assets_for_risk_profile(risk_profile)
        
        # Apply dynamic filters
        filtered_assets = []
        
        for asset in base_assets:
            if asset in exclude_assets:
                continue
                
            try:
                # Skip if we've reached the desired count
                if count and len(filtered_assets) >= count:
                    break
                
                # Additional real-time filtering could go here
                # For example, checking current liquidity, recent volatility, etc.
                
                # Basic check: get recent data to ensure asset is still viable
                df = get_historical_data(asset, interval='1h', lookback_periods=10)
                
                # Check for sufficient recent data
                if len(df) >= 5:
                    # Check for extreme recent moves (>20% in last few hours)
                    recent_returns = df['close'].pct_change().dropna()
                    max_recent_return = recent_returns.abs().max() if len(recent_returns) > 0 else 0
                    
                    # Skip assets with extreme recent moves (>20% in recent data)
                    if max_recent_return <= 0.20:  # 20% threshold
                        filtered_assets.append(asset)
                        
            except Exception as e:
                print(f"Error filtering asset {asset}: {e}")
                # Skip this asset but continue processing others
                continue
        
        # If we don't have enough assets after filtering, or if we want to ensure diversity,
        # we'll try to select a more diverse set from the available assets
        if count and len(filtered_assets) < count:
            # Collect all viable assets (even if we already have some)
            all_viable_assets = filtered_assets[:]
            added_assets = set(filtered_assets)
            
            # Add more assets from the base list that haven't been added yet
            for asset in base_assets:
                if (asset not in added_assets and 
                    asset not in exclude_assets and 
                    len(all_viable_assets) < count):
                    try:
                        # Verify the asset is still viable
                        df = get_historical_data(asset, interval='1h', lookback_periods=10)
                        if len(df) >= 5:
                            recent_returns = df['close'].pct_change().dropna()
                            max_recent_return = recent_returns.abs().max() if len(recent_returns) > 0 else 0
                            
                            if max_recent_return <= 0.25:  # Slightly more lenient for additional assets
                                all_viable_assets.append(asset)
                                added_assets.add(asset)
                    except Exception:
                        continue  # Skip if there's an issue with this asset
        
            # If we still need more assets and want diversity, we can try to include some even with stricter recent moves
            if count and len(all_viable_assets) < count:
                for asset in base_assets:
                    if (asset not in added_assets and 
                        asset not in exclude_assets and 
                        len(all_viable_assets) < count):
                        try:
                            df = get_historical_data(asset, interval='1h', lookback_periods=10)
                            if len(df) >= 5:
                                recent_returns = df['close'].pct_change().dropna()
                                max_recent_return = recent_returns.abs().max() if len(recent_returns) > 0 else 0
                                
                                # More lenient threshold for final additions
                                if max_recent_return <= 0.30:  # Even more lenient for final assets
                                    all_viable_assets.append(asset)
                                    added_assets.add(asset)
                        except Exception:
                            continue  # Skip if there's an issue with this asset
        
            return all_viable_assets[:count] if count else all_viable_assets
        else:
            # If we have enough filtered assets, just return them
            return filtered_assets[:count] if count else filtered_assets


# Global instance for easy access
asset_selector = DynamicAssetSelector()


def get_risk_appropriate_assets(risk_profile: str, count: int = 6) -> list:
    """
    Public function to get assets appropriate for a risk profile
    """
    return asset_selector.select_assets(risk_profile, count)