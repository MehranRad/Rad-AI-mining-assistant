'use client'

import { useEffect, useState } from 'react'
import { Users, Cog, Activity, TrendingUp } from 'lucide-react'
import { getStats, Stats } from '@/lib/api'

const cardConfig = [
  { key: 'employees', label: 'کل کارکنان', icon: Users, format: (v: number | null) => v ?? '—' },
  { key: 'equipment', label: 'کل تجهیزات', icon: Cog, format: (v: number | null) => v ?? '—' },
  { key: 'running', label: 'تجهیزات فعال', icon: Activity, format: (v: number | null) => v ?? '—' },
  {
    key: 'recovery',
    label: 'میانگین نرخ بازیابی',
    icon: TrendingUp,
    format: (v: number | null) => (v !== null ? `${v.toFixed(1)}%` : '—'),
  },
] as const

export function KpiCards() {
  const [stats, setStats] = useState<Stats | null>(null)

  useEffect(() => {
    getStats().then(setStats).catch(() => setStats(null))
  }, [])

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {cardConfig.map(({ key, label, icon: Icon, format }) => (
        <div
          key={key}
          className="bg-neutral-900/60 border border-neutral-800 rounded-xl p-4 flex flex-col gap-2 backdrop-blur-sm"
        >
          <Icon size={17} className="text-neutral-500" />
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-white font-en">
              {stats ? format(stats[key as keyof Stats]) : '—'}
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#E08A4F]" />
          </div>
          <span className="text-xs text-neutral-400">{label}</span>
        </div>
      ))}
    </div>
  )
}