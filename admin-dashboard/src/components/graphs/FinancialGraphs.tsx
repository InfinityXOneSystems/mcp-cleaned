import React, { useMemo } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Area, AreaChart } from 'recharts'
import type { GraphConfig } from '@/types'
import { useTheme } from '@/lib/theme'

interface FinancialGraphProps {
  config: GraphConfig
  height?: number
}

/**
 * Real Estate Price Trend Graph
 * Shows predicted (blue dotted) vs actual (neon green solid)
 */
export function RealEstatePriceGraph({ config, height = 300 }: FinancialGraphProps) {
  const theme = useTheme()
  
  const data = useMemo(() => {
    return config.dataPoints.map(point => ({
      date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      actual: point.actual || point.value,
      predicted: point.predicted,
      confidence: point.confidence,
    }))
  }, [config.dataPoints])

  return (
    <div className="glass-panel p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-glow">{config.title}</h3>
        {config.description && <p className="text-sm text-slate-light mt-1">{config.description}</p>}
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.neon_green} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={theme.neon_green} stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorPredicted" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={theme.electric_blue} stopOpacity={0.1}/>
              <stop offset="95%" stopColor={theme.electric_blue} stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 102, 255, 0.1)" />
          <XAxis dataKey="date" stroke={theme.text_muted} />
          <YAxis stroke={theme.text_muted} />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(10, 10, 10, 0.9)',
              border: `1px solid ${theme.electric_blue}`,
              borderRadius: '8px',
            }}
            labelStyle={{ color: theme.text_primary }}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="actual" 
            fill="url(#colorActual)" 
            stroke={theme.neon_green}
            strokeWidth={2}
            name="Actual Price"
          />
          <Line 
            type="monotone" 
            dataKey="predicted" 
            stroke={theme.electric_blue}
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Predicted Price"
            dot={false}
          />
        </ComposedChart>
      </ResponsiveContainer>

      <div className="mt-4 text-xs text-slate-light">
        <p>📊 Green solid = Real-time actuals | 🔵 Blue dotted = Predictions</p>
        {config.confidence && <p>Confidence: {config.confidence.toUpperCase()}</p>}
      </div>
    </div>
  )
}

/**
 * Loan Demand Signal Graph
 */
export function LoanDemandGraph({ config, height = 300 }: FinancialGraphProps) {
  const theme = useTheme()
  
  const data = useMemo(() => {
    return config.dataPoints.map(point => ({
      date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      value: Math.round(point.value),
      confidence: (point.confidence || 0.8) * 100,
    }))
  }, [config.dataPoints])

  return (
    <div className="glass-panel p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-glow">{config.title}</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 102, 255, 0.1)" />
          <XAxis dataKey="date" stroke={theme.text_muted} />
          <YAxis stroke={theme.text_muted} />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(10, 10, 10, 0.9)',
              border: `1px solid ${theme.electric_blue}`,
            }}
            labelStyle={{ color: theme.text_primary }}
          />
          <Bar dataKey="value" fill={theme.electric_blue} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Buy/Sell/Hold Indicator Graph
 */
export function BuySellHoldGraph({ config, height = 300 }: FinancialGraphProps) {
  const theme = useTheme()
  
  const data = useMemo(() => {
    return config.dataPoints.map(point => {
      const v = point.value
      return {
        date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        buy: v > 0.6 ? 1 : 0,
        hold: (v >= 0.4 && v <= 0.6) ? 1 : 0,
        sell: v < 0.4 ? 1 : 0,
      }
    })
  }, [config.dataPoints])

  return (
    <div className="glass-panel p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-glow">{config.title}</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 102, 255, 0.1)" />
          <XAxis dataKey="date" stroke={theme.text_muted} />
          <YAxis stroke={theme.text_muted} />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(10, 10, 10, 0.9)',
              border: `1px solid ${theme.electric_blue}`,
            }}
            labelStyle={{ color: theme.text_primary }}
          />
          <Bar dataKey="buy" stackId="a" fill={theme.success} name="Buy" />
          <Bar dataKey="hold" stackId="a" fill={theme.warning} name="Hold" />
          <Bar dataKey="sell" stackId="a" fill={theme.error} name="Sell" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * Market Sentiment Trend
 */
export function MarketSentimentGraph({ config, height = 300 }: FinancialGraphProps) {
  const theme = useTheme()
  
  const data = useMemo(() => {
    return config.dataPoints.map(point => ({
      date: new Date(point.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      sentiment: (point.value - 0.5) * 2, // normalize to -1 to 1
      volume: Math.round(point.confidence || 1),
    }))
  }, [config.dataPoints])

  return (
    <div className="glass-panel p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-glow">{config.title}</h3>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 102, 255, 0.1)" />
          <XAxis dataKey="date" stroke={theme.text_muted} />
          <YAxis stroke={theme.text_muted} domain={[-1, 1]} />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(10, 10, 10, 0.9)',
              border: `1px solid ${theme.electric_blue}`,
            }}
            labelStyle={{ color: theme.text_primary }}
            formatter={(value) => {
              if (value > 0) return [`Bullish +${(value * 100).toFixed(0)}%`, 'Sentiment']
              return [`Bearish ${(value * 100).toFixed(0)}%`, 'Sentiment']
            }}
          />
          <Line 
            type="monotone" 
            dataKey="sentiment" 
            stroke={theme.electric_blue}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-3 gap-2 text-xs">
        <div className="text-center">
          <p className="text-neon-green">BULLISH</p>
          <p className="text-slate-light">&gt; 0.5</p>
        </div>
        <div className="text-center">
          <p className="text-warning">NEUTRAL</p>
          <p className="text-slate-light">0.4 - 0.6</p>
        </div>
        <div className="text-center">
          <p className="text-error">BEARISH</p>
          <p className="text-slate-light">&lt; 0.4</p>
        </div>
      </div>
    </div>
  )
}
