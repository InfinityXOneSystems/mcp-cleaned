import React, { useState, useEffect } from 'react'
import { TrendingUp, AlertCircle, Zap, Brain } from 'lucide-react'
import { RealEstatePriceGraph, MarketSentimentGraph, BuySellHoldGraph } from '@/components/graphs/FinancialGraphs'
import { realEstateService, loanSignalService } from '@/services/firestore'
import type { RealEstateProperty, LoanSignal } from '@/types'
import { useTheme } from '@/lib/theme'

/**
 * Center Panel - Core Intelligence
 * Real Estate, Funding, Leads, Predictions
 */
export function CenterPanel() {
  const theme = useTheme()
  const [activeTab, setActiveTab] = useState<'real-estate' | 'lending' | 'sentiment' | 'predictions'>('real-estate')
  const [properties, setProperties] = useState<RealEstateProperty[]>([])
  const [loanSignals, setLoanSignals] = useState<LoanSignal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      try {
        const [props, signals] = await Promise.all([
          realEstateService.getProperties(10),
          loanSignalService.getSignals(10),
        ])
        setProperties(props)
        setLoanSignals(signals)
      } catch (err) {
        console.error('Failed to load data:', err)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [])

  return (
    <div className="glass-panel p-6 h-full overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-glow">Intelligence Cockpit</h1>
        <p className="text-slate-light mt-2">Real-time market signals, predictions & opportunities</p>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 mb-6 border-b border-glass pb-4">
        {[
          { id: 'real-estate', label: 'Real Estate', icon: '🏠' },
          { id: 'lending', label: 'Funding Intelligence', icon: '💰' },
          { id: 'sentiment', label: 'Market Sentiment', icon: '📊' },
          { id: 'predictions', label: 'Forecasts', icon: '🔮' },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id
                ? 'bg-electric-blue text-white shadow-glow-blue'
                : 'bg-glass-accent text-slate-light hover:text-white'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'real-estate' && <RealEstateTab properties={properties} />}
      {activeTab === 'lending' && <LendingTab signals={loanSignals} />}
      {activeTab === 'sentiment' && <SentimentTab />}
      {activeTab === 'predictions' && <PredictionsTab />}
    </div>
  )
}

function RealEstateTab({ properties }: { properties: RealEstateProperty[] }) {
  const theme = useTheme()

  return (
    <div className="space-y-4">
      {/* Graph */}
      <RealEstatePriceGraph
        config={{
          title: 'Real Estate Price Trends',
          description: 'Distressed property value predictions vs market actuals',
          metric: 'average-price',
          dataPoints: [
            { timestamp: new Date(Date.now() - 86400000 * 30), value: 450000, predicted: 460000, confidence: 0.92 },
            { timestamp: new Date(Date.now() - 86400000 * 20), value: 440000, predicted: 455000, confidence: 0.89 },
            { timestamp: new Date(Date.now() - 86400000 * 10), value: 435000, predicted: 450000, confidence: 0.85 },
            { timestamp: new Date(Date.now()), value: 428000, predicted: 440000, confidence: 0.92 },
          ],
          unit: 'USD',
          confidence: 'high',
        }}
      />

      {/* Properties List */}
      <div>
        <h3 className="text-lg font-semibold mb-4 text-electric-blue-light">Distressed Properties</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {properties.slice(0, 6).map(prop => (
            <div key={prop.id} className="bg-glass-accent border border-glass rounded-lg p-3">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-medium text-white">{prop.address}</p>
                  <p className="text-xs text-slate-light">{prop.city}, {prop.state}</p>
                </div>
                <div className={`text-xs px-2 py-1 rounded font-medium ${
                  prop.distressScore > 70 ? 'bg-error text-white' : 'bg-warning text-black'
                }`}>
                  {prop.distressScore}% Distress
                </div>
              </div>
              <div className="text-xs text-slate-light space-y-1">
                <p>💰 List: ${prop.price.toLocaleString()} | Est: ${(prop.estimatedValue || prop.price).toLocaleString()}</p>
                <p>📏 {prop.beds}bd {prop.baths}ba | {prop.sqft} sqft</p>
              </div>
              <button className="w-full mt-2 text-xs py-1 bg-electric-blue hover:bg-electric-blue-light rounded transition">
                View Deal
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function LendingTab({ signals }: { signals: LoanSignal[] }) {
  return (
    <div className="space-y-4">
      <div className="bg-glass-accent border border-glass rounded-lg p-4 mb-4">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="text-neon-green" size={20} />
          <h3 className="text-lg font-semibold">Funding Opportunities</h3>
        </div>
        <p className="text-sm text-slate-light">
          {signals.length} active opportunities identified across lending markets
        </p>
      </div>

      <div className="space-y-3">
        {signals.slice(0, 5).map(signal => (
          <div key={signal.id} className="bg-glass-accent border border-glass rounded-lg p-3">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="font-medium text-white">{signal.businessName}</p>
                <p className="text-xs text-slate-light">{signal.borrowerType.toUpperCase()}</p>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-neon-green">${(signal.loanAmount / 1000000).toFixed(1)}M</p>
                <p className="text-xs text-slate-light">{signal.loanType}</p>
              </div>
            </div>
            <div className="flex gap-2 items-center mb-2">
              <div className="flex-1 bg-glass rounded h-2">
                <div
                  className="bg-gradient-to-r from-electric-blue to-neon-green h-2 rounded"
                  style={{ width: `${signal.urgencyScore}%` }}
                ></div>
              </div>
              <span className="text-xs text-neon-green font-medium">{signal.urgencyScore}% Urgent</span>
            </div>
            <p className="text-xs text-slate-light mb-2">{signal.purpose}</p>
            <button className="text-xs py-1 px-2 bg-electric-blue rounded hover:bg-electric-blue-light transition">
              Contact Lead
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

function SentimentTab() {
  return (
    <div className="space-y-4">
      <MarketSentimentGraph
        config={{
          title: 'Market Sentiment Analysis',
          description: 'Real-time social & news sentiment across financial markets',
          metric: 'sentiment-score',
          dataPoints: [
            { timestamp: new Date(Date.now() - 86400000 * 7), value: 0.55, confidence: 0.8 },
            { timestamp: new Date(Date.now() - 86400000 * 5), value: 0.62, confidence: 0.85 },
            { timestamp: new Date(Date.now() - 86400000 * 3), value: 0.58, confidence: 0.82 },
            { timestamp: new Date(Date.now() - 86400000), value: 0.65, confidence: 0.88 },
            { timestamp: new Date(Date.now()), value: 0.72, confidence: 0.91 },
          ],
        }}
        height={350}
      />
      <div className="grid grid-cols-3 gap-4 mt-4">
        <StatCard title="Bullish Signals" value="47" trend="↑ +12%" color="neon-green" />
        <StatCard title="Neutral" value="31" trend="stable" color="warning" />
        <StatCard title="Bearish" value="22" trend="↓ -5%" color="error" />
      </div>
    </div>
  )
}

function PredictionsTab() {
  return (
    <div className="space-y-4">
      <BuySellHoldGraph
        config={{
          title: 'Buy/Sell/Hold Indicators',
          metric: 'buy-sell-hold',
          dataPoints: [
            { timestamp: new Date(Date.now() - 86400000 * 10), value: 0.7, confidence: 0.85 },
            { timestamp: new Date(Date.now() - 86400000 * 5), value: 0.65, confidence: 0.82 },
            { timestamp: new Date(Date.now()), value: 0.72, confidence: 0.91 },
          ],
        }}
        height={350}
      />
      <div className="grid grid-cols-3 gap-4 mt-4">
        <StatCard title="Buy Signals" value="12" trend="Strong" color="neon-green" />
        <StatCard title="Hold" value="8" trend="Wait" color="warning" />
        <StatCard title="Sell Signals" value="3" trend="Exit" color="error" />
      </div>
    </div>
  )
}

function StatCard({ title, value, trend, color }: any) {
  const colorMap = {
    'neon-green': 'text-neon-green',
    'warning': 'text-warning',
    'error': 'text-error',
  }
  return (
    <div className="bg-glass-accent border border-glass rounded-lg p-4">
      <p className="text-xs text-slate-light mb-2">{title}</p>
      <p className={`text-2xl font-bold ${colorMap[color]}`}>{value}</p>
      <p className="text-xs text-slate-light mt-1">{trend}</p>
    </div>
  )
}
