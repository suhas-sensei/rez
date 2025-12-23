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
  price: number;
  size: number;
  timestamp: string;
}

interface AgentStatus {
  running: boolean;
  paused: boolean;
  assets: string[];
  risk_profile: string;
}

export default function Dashboard() {
  const { ready, authenticated, user, logout } = usePrivy();
  const { wallets } = useWallets();
  const router = useRouter();
  const hasInitialized = useRef(false);

  const [portfolio, setPortfolio] = useState<any>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
  const [fundingStatus, setFundingStatus] = useState<string>("");

  // Agent config
  const [selectedAssets, setSelectedAssets] = useState(["BTC", "ETH"]);
  const [riskProfile, setRiskProfile] = useState("medium");

  const embeddedWallet = wallets.find((w) => w.walletClientType === "privy");
  const walletAddress = embeddedWallet?.address;

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

  async function fetchPortfolio(address: string) {
    try {
      const res = await fetch(`${API_URL}/portfolio?wallet_address=${address}`);
      if (res.ok) {
        const data = await res.json();
        setPortfolio(data);
        setPositions(data.positions || []);
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
      const res = await fetch(`${API_URL}/trading/history?limit=10`);
      if (res.ok) {
        const data = await res.json();
        setTrades(data.trades || []);
      }
    } catch (e) {
      console.error("Failed to fetch trades:", e);
    }
  }

  // Initialize data
  useEffect(() => {
    if (!ready || !authenticated || !walletAddress || !user?.id) return;
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    // Use setTimeout to avoid linter warning about sync setState in effect
    setTimeout(() => {
      registerAndFund(user.id, walletAddress);
      fetchPortfolio(walletAddress);
      fetchAgentStatus();
      fetchTrades();
    }, 0);
  }, [ready, authenticated, walletAddress, user?.id]);

  // Polling
  useEffect(() => {
    if (!ready || !authenticated || !walletAddress) return;

    const interval = setInterval(() => {
      fetchPortfolio(walletAddress);
      fetchAgentStatus();
      fetchTrades();
    }, 5000);

    return () => clearInterval(interval);
  }, [ready, authenticated, walletAddress]);

  // Agent controls
  const startAgent = async () => {
    await fetch(`${API_URL}/agent/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        assets: selectedAssets,
        risk_profile: riskProfile,
        interval_seconds: 60,
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
              onClick={logout}
              className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Account Value</p>
            <p className="text-3xl font-bold">
              ${portfolio?.account_value?.toFixed(2) || "0.00"}
            </p>
          </div>
          <div className="bg-gray-800 rounded-xl p-6">
            <p className="text-gray-400 text-sm">Available Balance</p>
            <p className="text-3xl font-bold">
              ${portfolio?.available_balance?.toFixed(2) || "0.00"}
            </p>
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
            <div className="flex flex-wrap gap-4 items-end">
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Assets
                </label>
                <select
                  multiple
                  value={selectedAssets}
                  onChange={(e) =>
                    setSelectedAssets(
                      Array.from(e.target.selectedOptions, (o) => o.value)
                    )
                  }
                  className="bg-gray-700 rounded-lg p-2 min-w-[150px]"
                >
                  {["BTC", "ETH", "SOL", "AVAX", "ARB", "DOGE"].map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-1">
                  Risk Profile
                </label>
                <select
                  value={riskProfile}
                  onChange={(e) => setRiskProfile(e.target.value)}
                  className="bg-gray-700 rounded-lg p-2"
                >
                  <option value="low">Low Risk</option>
                  <option value="medium">Medium Risk</option>
                  <option value="high">High Risk</option>
                </select>
              </div>
              <div className="flex gap-2">
                {!agentStatus?.running ? (
                  <button
                    onClick={startAgent}
                    className="px-6 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold"
                  >
                    Start Agent
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
                      className="px-6 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-semibold"
                    >
                      Stop
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
                    Requires strong indicator agreement. Smaller positions,
                    fewer trades.
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
                    Balanced approach. Moderate position sizes and trade
                    frequency.
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
                    Lower signal requirements. Larger positions, more frequent
                    trades.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Positions */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Open Positions</h2>
          {positions.length === 0 ? (
            <p className="text-gray-500">No open positions</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm">
                  <th className="pb-2">Asset</th>
                  <th className="pb-2">Size</th>
                  <th className="pb-2">Entry Price</th>
                  <th className="pb-2">PnL</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, i) => (
                  <tr key={i} className="border-t border-gray-700">
                    <td className="py-3 font-semibold">{pos.asset}</td>
                    <td
                      className={
                        pos.size > 0 ? "text-green-400" : "text-red-400"
                      }
                    >
                      {pos.size > 0 ? "+" : ""}
                      {pos.size.toFixed(4)}
                    </td>
                    <td>${pos.entry_price.toFixed(2)}</td>
                    <td
                      className={
                        pos.unrealized_pnl >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      ${pos.unrealized_pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Recent Trades */}
        <div className="bg-gray-800 rounded-xl p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Trades</h2>
          {trades.length === 0 ? (
            <p className="text-gray-500">No trades yet</p>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="text-left text-gray-400 text-sm">
                  <th className="pb-2">Time</th>
                  <th className="pb-2">Asset</th>
                  <th className="pb-2">Side</th>
                  <th className="pb-2">Size</th>
                  <th className="pb-2">Price</th>
                </tr>
              </thead>
              <tbody>
                {trades.map((trade, i) => (
                  <tr key={i} className="border-t border-gray-700">
                    <td className="py-3 text-gray-400 text-sm">
                      {new Date(trade.timestamp).toLocaleTimeString()}
                    </td>
                    <td className="font-semibold">{trade.asset}</td>
                    <td
                      className={
                        trade.decision === "BUY"
                          ? "text-green-400"
                          : "text-red-400"
                      }
                    >
                      {trade.decision}
                    </td>
                    <td>{trade.size?.toFixed(4)}</td>
                    <td>${trade.price?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>
    </div>
  );
}
