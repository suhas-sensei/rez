"use client";

import { usePrivy } from "@privy-io/react-auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const { login, authenticated, ready } = usePrivy();
  const router = useRouter();

  useEffect(() => {
    if (ready && authenticated) {
      router.push("/dashboard");
    }
  }, [ready, authenticated, router]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-gray-900 to-black flex flex-col items-center justify-center p-8">
      <div className="max-w-md w-full space-y-8 text-center">
        {/* Logo/Title */}
        <div>
          <h1 className="text-5xl font-bold text-white mb-2">Rez</h1>
          <p className="text-purple-400 text-xl">AI Trading Agent</p>
        </div>

        {/* Description */}
        <div className="space-y-4 text-gray-300">
          <p className="text-lg">
            Autonomous trading powered by AI on Hyperliquid
          </p>
          <div className="flex justify-center gap-4 text-sm">
            <span className="px-3 py-1 bg-purple-900/50 rounded-full">
              Real-time Analysis
            </span>
            <span className="px-3 py-1 bg-purple-900/50 rounded-full">
              Multi-Asset
            </span>
            <span className="px-3 py-1 bg-purple-900/50 rounded-full">
              Risk Management
            </span>
          </div>
        </div>

        {/* Login Button */}
        <div className="pt-8">
          {!ready ? (
            <div className="text-gray-400">Loading...</div>
          ) : (
            <button
              onClick={login}
              className="w-full py-4 px-6 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-lg transition-colors duration-200 text-lg"
            >
              Get Started
            </button>
          )}
        </div>

        {/* Footer */}
        <p className="text-gray-500 text-sm pt-8">
          Testnet Mode • No real funds at risk
        </p>
      </div>
    </main>
  );
}
