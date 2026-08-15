'use client'

import { useState } from 'react'
import { Eye, EyeOff, Loader2, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

export function LoginForm() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!username.trim() || !password.trim()) {
      setError('نام کاربری و رمز عبور را وارد کنید.')
      return
    }

    setIsLoading(true)
    try {
      await new Promise((resolve) => setTimeout(resolve, 900))
      setError('اتصال به سرور هنوز پیاده‌سازی نشده است.')
    } catch {
      setError('نام کاربری یا رمز عبور اشتباه است.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-full max-w-sm mx-auto">
      <div className="flex items-center gap-3 mb-10">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] flex items-center justify-center shadow-[0_0_20px_-4px_rgba(224,138,79,0.6)]">
          <span className="font-en text-white font-bold text-sm">Rad</span>
        </div>
        <div>
          <p className="font-en text-white font-semibold leading-none">Rad AI</p>
          <p className="font-en text-neutral-500 text-xs mt-1">Mining Intelligence Assistant</p>
        </div>
      </div>

      <h1 className="text-2xl font-semibold text-white mb-2">خوش آمدید</h1>
      <p className="text-neutral-400 text-sm mb-8">
        برای ورود به دستیار هوشمند معدن مس، اطلاعات کاربری خود را وارد کنید.
      </p>

      <form onSubmit={handleSubmit} className="space-y-5" dir="rtl">
        <div className="space-y-2">
          <Label htmlFor="username" className="text-neutral-300">
            نام کاربری
          </Label>
          <Input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="نام کاربری خود را وارد کنید"
            autoComplete="username"
            dir="rtl"
            className="bg-neutral-900/80 border-neutral-700 text-white placeholder:text-neutral-500 focus-visible:ring-[#E08A4F]/50 focus-visible:border-[#E08A4F]/70 h-11"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="password" className="text-neutral-300">
            رمز عبور
          </Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="رمز عبور خود را وارد کنید"
              autoComplete="current-password"
              dir="rtl"
              className="bg-neutral-900/80 border-neutral-700 text-white placeholder:text-neutral-500 focus-visible:ring-[#E08A4F]/50 focus-visible:border-[#E08A4F]/70 h-11 pl-11"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-500 hover:text-neutral-300 transition-colors"
              aria-label={showPassword ? 'مخفی کردن رمز عبور' : 'نمایش رمز عبور'}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Checkbox
            id="remember"
            checked={rememberMe}
            onCheckedChange={(v) => setRememberMe(v === true)}
            className="border-neutral-700 data-[state=checked]:bg-[#E08A4F] data-[state=checked]:border-[#E08A4F]"
          />
          <Label htmlFor="remember" className="text-neutral-400 text-sm font-normal cursor-pointer">
            مرا به خاطر بسپار
          </Label>
        </div>

        {error && (
          <div className="flex items-start gap-2 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-md px-3 py-2.5">
            <AlertCircle size={16} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full h-11 bg-[#B5723A] hover:bg-[#8B4A28] text-white font-medium transition-colors"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Loader2 size={16} className="animate-spin" />
              در حال ورود...
            </span>
          ) : (
            'ورود'
          )}
        </Button>
      </form>

      <p className="font-en text-neutral-600 text-xs text-center mt-10">
        Rad AI v0.1 · Prototype · اجرای محلی
      </p>
    </div>
  )
}