"use client";

import { usePrivy, useWallets } from "@privy-io/react-auth";
import { useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Position {
  asset: string;
  size: number;
  entry_price: number;
  unrealized_pnl: number;
}

interface Trade {
  asset: string;
  decision: string;
  side?: string;
  price: number;
  size: number;
  value?: number;
  entry_price?: number;
  timestamp: string;
  pnl?: number | null;
}

interface AgentStatus {
  running: boolean;
  paused: boolean;
  assets: string[];
  risk_profile: string;
  betting_amount: number;
  open_position: {
    asset: string;
    side: string;
    size: number;
    entry_price: number;
    entry_value: number;
    entry_time: string;
  } | null;
  realized_pnl: number;
}

interface PortfolioHistory {
  timestamp: string;
  value: number;
}

interface Portfolio {
  account_value: number;
  available_balance: number;
  positions: Position[];
}

export default function Dashboard() {
  const { ready, authenticated, user, logout } = usePrivy();
  const { wallets } = useWallets();
  const router = useRouter();
  const hasInitialized = useRef(false);

  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [fundingStatus, setFundingStatus] = useState<string>("");
  const [portfolioHistory, setPortfolioHistory] = useState<PortfolioHistory[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Agent config - ETH only (Hyperliquid min order is $10)
  const [bettingAmount, setBettingAmount] = useState(10);
  const [riskProfile, setRiskProfile] = useState("low");

  const embeddedWallet = wallets.find((w) => w.walletClientType === "privy");
  const walletAddress = embeddedWallet?.address;

  // P&L comes from backend (realized trades)
  const currentValue = portfolio?.account_value || 0;
  const realizedPnl = agentStatus?.realized_pnl || 0;
  const pnlPercent = bettingAmount > 0 ? ((realizedPnl / bettingAmount) * 100) : 0;

  // Redirect if not authenticated
  useEffect(() => {
    if (ready && !authenticated) {
      router.push("/");
    }
  }, [ready, authenticated, router]);

  // Fetch functions
  async function registerAndFund(userId: string, address: string) {
    try {
      setFundingStatus("Registering...");
      const res = await fetch(`${API_URL}/users/register-and-fund`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          privy_id: userId,
          wallet_address: address,
        }),
      });
      const data = await res.json();

      if (data.funding?.status === "completed") {
        setFundingStatus(`Funded ${data.funding.amount} USDC!`);
      } else if (data.funding?.status === "skipped") {
        setFundingStatus("Account ready");
      } else {
        setFundingStatus(data.funding?.message || "Ready");
      }
    } catch {
      setFundingStatus("Funding service unavailable");
    }
  }

  async function fetchPortfolio() {
    try {
      // Backend uses configured Hyperliquid wallet, not Privy wallet
      const res = await fetch(`${API_URL}/portfolio`);
      if (res.ok) {
        const data = await res.json();
        console.log("[DEBUG] Portfolio data:", data);
        setPortfolio(data);

        // Update portfolio history for chart
        if (data.account_value) {
          setPortfolioHistory(prev => {
            const newEntry = {
              timestamp: new Date().toISOString(),
              value: data.account_value
            };
            // Keep last 50 data points
            const updated = [...prev, newEntry].slice(-50);
            return updated;
          });
        }
      } else {
        console.error("[DEBUG] Portfolio fetch failed:", res.status);
      }
    } catch (e) {
      console.error("Failed to fetch portfolio:", e);
    }
  }

  async function fetchAgentStatus() {
    try {
      const res = await fetch(`${API_URL}/agent/status`);
      if (res.ok) {
        const data = await res.json();
        setAgentStatus(data);
      }
    } catch (e) {
      console.error("Failed to fetch agent status:", e);
    }
  }

  async function fetchTrades() {
    try {
      const res = await fetch(`${API_URL}/trading/history?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setTrades(data.trades || []);
      }
    } catch (e) {
      console.error("Failed to fetch trades:", e);
    }
  }

  // Manual refresh
  async function refreshData() {
    setIsRefreshing(true);
    await Promise.all([
      fetchPortfolio(),
      fetchAgentStatus(),
      fetchTrades()
    ]);
    setIsRefreshing(false);
  }

  // Initialize data
  useEffect(() => {
    if (!ready || !authenticated) return;
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    setTimeout(() => {
      // Register user if we have Privy ID and wallet
      if (user?.id && walletAddress) {
        registerAndFund(user.id, walletAddress);
      }
      // Always fetch portfolio (uses backend's configured wallet)
      fetchPortfolio();
      fetchAgentStatus();
      fetchTrades();
    }, 0);
  }, [ready, authenticated, walletAddress, user?.id]);

  // Polling
  useEffect(() => {
    if (!ready || !authenticated) return;

    const interval = setInterval(() => {
      fetchPortfolio();
      fetchAgentStatus();
      fetchTrades();
    }, 5000);

    return () => clearInterval(interval);
  }, [ready, authenticated]);

  // Agent controls
  const startAgent = async () => {
    await fetch(`${API_URL}/agent/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assets: ["ETH"],  // ETH only
        risk_profile: riskProfile,
        interval_seconds: 30,
        betting_amount: bettingAmount,
      }),
    });
    fetchAgentStatus();
  };

  const stopAgent = async () => {
    await fetch(`${API_URL}/agent/stop`, { method: "POST" });
    fetchAgentStatus();
  };

  const togglePause = async () => {
    const endpoint = agentStatus?.paused ? "/agent/resume" : "/agent/pause";
    await fetch(`${API_URL}${endpoint}`, { method: "POST" });
    fetchAgentStatus();
  };

  // Simple SVG line chart
  const renderChart = () => {
    if (portfolioHistory.length < 2) {
      return (
        <div className="h-64 flex items-center justify-center text-gray-500">
          Collecting data points...
        </div>
      );
    }

    const values = portfolioHistory.map(p => p.value);
    const minVal = Math.min(...values) * 0.999;
    const maxVal = Math.max(...values) * 1.001;
    const range = maxVal - minVal || 1;

    const width = 800;
    const height = 250;
    const padding = 40;

    const points = portfolioHistory.map((p, i) => {
      const x = padding + (i / (portfolioHistory.length - 1)) * (width - padding * 2);
      const y = height - padding - ((p.value - minVal) / range) * (height - padding * 2);
      return `${x},${y}`;
    }).join(" ");

    return (
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-64">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
          <g key={i}>
            <line
              x1={padding}
              y1={height - padding - ratio * (height - padding * 2)}
              x2={width - padding}
              y2={height - padding - ratio * (height - padding * 2)}
              stroke="#374151"
              strokeWidth="1"
            />
            <text
              x={padding - 5}
              y={height - padding - ratio * (height - padding * 2) + 4}
              fill="#9CA3AF"
              fontSize="10"
              textAnchor="end"
            >
              ${(minVal + ratio * range).toFixed(2)}
            </text>
          </g>
        ))}

        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke="#10B981"
          strokeWidth="2"
        />

        {/* Data points */}
        {portfolioHistory.map((p, i) => {
          const x = padding + (i / (portfolioHistory.length - 1)) * (width - padding * 2);
          const y = height - padding - ((p.value - minVal) / range) * (height - padding * 2);
          return (
            <circle key={i} cx={x} cy={y} r="3" fill="#10B981" />
          );
        })}

        {/* X-axis labels */}
        {portfolioHistory.length > 0 && (
          <>
            <text x={padding} y={height - 10} fill="#9CA3AF" fontSize="10">
              {new Date(portfolioHistory[0].timestamp).toLocaleTimeString()}
            </text>
            <text x={width - padding} y={height - 10} fill="#9CA3AF" fontSize="10" textAnchor="end">
              {new Date(portfolioHistory[portfolioHistory.length - 1].timestamp).toLocaleTimeString()}
            </text>
          </>
        )}
      </svg>
    );
  };

  // Show loading only while Privy is initializing
  if (!ready) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 p-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-purple-400">Rez Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">
              {walletAddress?.slice(0, 6)}...
              {walletAddress?.slice(-4)}
            </span>
            <span className="text-sm text-green-400">{fundingStatus}</span>
            <button
              onClick={refreshData}
              disabled={isRefreshing}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded-lg text-sm flex items-center gap-2"
            >
              {isRefreshing ? (
                <span className="animate-spin">&#8635;</span>
              ) : (
                <span>&#8635;</span>
              )}
              Refresh Data
            </button>
            <button
              onClick={logout}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Status Banner */}
        {agentStatus?.running && (
          <div className="bg-blue-900/50 border border-blue-700 rounded-lg p-4">
            Trading session is currently running. Data refreshes automatically every 5 seconds.
          </div>
        )}

        {/* Portfolio Chart */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span className="text-green-400">&#x1F4C8;</span> Portfolio Value Over Time
          </h2>
          {renderChart()}
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Account Balance</p>
            <p className="text-3xl font-bold">
              ${currentValue.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Realized P&L</p>
            <p className={`text-3xl font-bold ${realizedPnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ${realizedPnl.toFixed(2)}
            </p>
            <span className={`text-sm px-2 py-1 rounded ${realizedPnl >= 0 ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}`}>
              {realizedPnl >= 0 ? "↑" : "↓"} {Math.abs(pnlPercent).toFixed(2)}%
            </span>
          </div>
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Betting Amount</p>
            <p className="text-3xl font-bold">${agentStatus?.betting_amount || bettingAmount}</p>
          </div>
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Agent Status</p>
            <p className="text-3xl font-bold">
              {agentStatus?.running ? (
                <span className="text-green-400">
                  {agentStatus.paused ? "Paused" : "Running"}
                </span>
              ) : (
                <span className="text-gray-500">Stopped</span>
              )}
            </p>
          </div>
        </div>

        {/* Agent Controls */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Agent Controls</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Left: Controls */}
            <div className="space-y-4">
              <div className="flex flex-wrap gap-4 items-end">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Market
                  </label>
                  <div className="bg-gray-700 rounded-lg p-2 px-4 font-semibold text-green-400">
                    ETH/USD
                  </div>
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Betting Amount ($)
                  </label>
                  <input
                    type="number"
                    value={bettingAmount}
                    onChange={(e) => setBettingAmount(Number(e.target.value))}
                    className="bg-gray-700 rounded-lg p-2 w-32"
                    min={10}
                    max={currentValue || 1000}
                    disabled={agentStatus?.running}
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">
                    Risk Profile
                  </label>
                  <select
                    value={riskProfile}
                    onChange={(e) => setRiskProfile(e.target.value)}
                    className="bg-gray-700 rounded-lg p-2"
                    disabled={agentStatus?.running}
                  >
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-2">
                {!agentStatus?.running ? (
                  <button
                    onClick={startAgent}
                    className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold flex items-center gap-2"
                  >
                    <span>&#x1F680;</span> Start Trading
                  </button>
                ) : (
                  <>
                    <button
                      onClick={togglePause}
                      className="px-6 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg font-semibold"
                    >
                      {agentStatus.paused ? "Resume" : "Pause"}
                    </button>
                    <button
                      onClick={stopAgent}
                      className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold flex items-center gap-2"
                    >
                      <span>&#x1F6D1;</span> Stop Trading
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Right: Risk Profile Details */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-gray-400 mb-3">
                {riskProfile.toUpperCase()} RISK SETTINGS
              </h3>
              {riskProfile === "low" && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Position Size</span>
                    <span className="text-white">1.5%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Kelly Fraction</span>
                    <span className="text-white">10%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Signal Threshold</span>
                    <span className="text-white">0.50 (Conservative)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Portfolio Risk</span>
                    <span className="text-white">10%</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-700">
                    Requires strong indicator agreement. Smaller positions, fewer trades.
                  </p>
                </div>
              )}
              {riskProfile === "medium" && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Position Size</span>
                    <span className="text-white">2%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Kelly Fraction</span>
                    <span className="text-white">15%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Signal Threshold</span>
                    <span className="text-white">0.40 (Balanced)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Portfolio Risk</span>
                    <span className="text-white">15%</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-700">
                    Balanced approach. Moderate position sizes and trade frequency.
                  </p>
                </div>
              )}
              {riskProfile === "high" && (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Position Size</span>
                    <span className="text-white">3%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Kelly Fraction</span>
                    <span className="text-white">18%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Signal Threshold</span>
                    <span className="text-white">0.35 (Aggressive)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Max Portfolio Risk</span>
                    <span className="text-white">20%</span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-700">
                    Lower signal requirements. Larger positions, more frequent trades.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Open Position */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Open Position</h2>
          {agentStatus?.open_position ? (
            <div className="bg-gray-900 rounded-lg p-4">
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div>
                  <p className="text-gray-400 text-sm">Asset</p>
                  <p className="font-bold text-lg">{agentStatus.open_position.asset}/USD</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Side</p>
                  <p className="font-bold text-lg text-green-400">{agentStatus.open_position.side}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Size</p>
                  <p className="font-bold text-lg">{agentStatus.open_position.size.toFixed(4)} ETH</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Entry Price</p>
                  <p className="font-bold text-lg">${agentStatus.open_position.entry_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Entry Value</p>
                  <p className="font-bold text-lg">${agentStatus.open_position.entry_value.toFixed(2)}</p>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No open position. Agent will open when BUY signal triggers.</p>
          )}
        </div>

        {/* Recent Trades */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Trade History ({trades.length})</h2>
          {trades.length === 0 ? (
            <p className="text-gray-500">No trades yet. Start the agent to begin trading.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-gray-400 text-sm">
                    <th className="pb-2">Time</th>
                    <th className="pb-2">Action</th>
                    <th className="pb-2">Size</th>
                    <th className="pb-2">Price</th>
                    <th className="pb-2">Value</th>
                    <th className="pb-2">P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {[...trades].reverse().map((trade: Trade, i) => (
                    <tr key={i} className="border-t border-gray-700">
                      <td className="py-3 text-gray-400 text-sm">
                        {new Date(trade.timestamp).toLocaleString()}
                      </td>
                      <td className={trade.side === "OPEN_LONG" ? "text-green-400 font-semibold" : "text-red-400 font-semibold"}>
                        {trade.side || trade.decision}
                      </td>
                      <td>{trade.size?.toFixed(4)} ETH</td>
                      <td>${trade.price?.toFixed(2)}</td>
                      <td>${trade.value?.toFixed(2) || "-"}</td>
                      <td className={trade.pnl === null || trade.pnl === undefined ? "text-gray-500" : (trade.pnl >= 0 ? "text-green-400 font-bold" : "text-red-400 font-bold")}>
                        {trade.pnl !== null && trade.pnl !== undefined ? `$${trade.pnl.toFixed(2)}` : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Risk Profile Footer */}
        <div className="bg-blue-900/30 border border-blue-800 rounded-lg p-4">
          <span className="text-gray-400">Risk Profile:</span>{" "}
          <span className="text-green-400 font-semibold capitalize">{riskProfile}</span>
        </div>
      </main>
    </div>
  );
}
