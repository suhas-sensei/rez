import sys
sys.path.append('src')
import pandas as pd
import json

trades = []
with open('trades_log.jsonl', 'r') as f:
    for line in f:
        try:
            trade = json.loads(line.strip())
            trades.append(trade)
        except:
            continue

print(f'Loaded {len(trades)} trades')

if trades:
    df = pd.DataFrame(trades)
    print('DataFrame columns:', list(df.columns))
    
    # Parse the timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Show portfolio values
    print()
    print('Portfolio values over time:')
    for i in range(len(df)):
        row = df.iloc[i]
        print(f'  {row["timestamp"]}: ${row["portfolio_value"]:.2f}')
        
    print(f"\nPortfolio value range: ${df['portfolio_value'].min():.2f} to ${df['portfolio_value'].max():.2f}")
else:
    print('No trades found')