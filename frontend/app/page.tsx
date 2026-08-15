import { LoginForm } from '@/components/login-form'
import { AICore } from '@/components/ui/ai-core'
import { Spotlight } from '@/components/ui/spotlight'

export default function Home() {
  return (
    <main className="min-h-screen w-full flex flex-col md:flex-row relative overflow-hidden">
      {/* Single unified glow across the ENTIRE page — no seam between sides */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(ellipse 90% 70% at 70% 50%, rgba(240,168,104,0.22) 0%, rgba(240,168,104,0.08) 40%, transparent 70%)',
        }}
      />

      <div className="w-full md:w-[42%] flex items-center justify-center px-6 py-16 relative z-10">
        <LoginForm />
      </div>

      <div className="hidden md:flex md:w-[58%] relative items-center justify-center z-10">
        <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="white" />
        <AICore />
        <div className="absolute bottom-10 left-1/2 -translate-x-1/2 text-center">
          <p className="font-en text-neutral-200 text-sm font-medium">Rad AI</p>
          <p className="text-neutral-400 text-xs mt-1">هوش مصنوعی تحلیل داده معدن مس</p>
        </div>
      </div>

      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-10">
        <p className="font-en text-neutral-500 text-[11px] tracking-wide">
          Built by Mehran Zamani Rad
        </p>
      </div>
    </main>
  )
}