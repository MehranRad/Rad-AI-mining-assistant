'use client'

const EXAMPLE_QUESTIONS = [
  'چند نفر کارمند در مجموعه داریم؟',
  'کدام معدن بیشترین تجهیزات را دارد؟',
  'میانگین حقوق در بخش تولید چقدر است؟',
  'چرا معدن سونگون نرخ بازیابی پایین‌تری دارد؟',
  'وضعیت تجهیزات هر معدن را مقایسه کن',
  'کدام معدن بیشترین ریسک را دارد؟',
]

export function EmptyState({ onPick }: { onPick: (q: string) => void }) {
  return (
    <div className="flex flex-col items-center text-center py-10 px-4" dir="rtl">
      <div className="relative w-16 h-16 mb-6 rounded-full bg-gradient-to-br from-[#E08A4F] to-[#8B4A28] flex items-center justify-center shadow-[0_0_40px_-8px_rgba(224,138,79,0.7)]">
        <span className="font-en text-white text-xl font-bold">R</span>
      </div>
      <h2 className="text-xl font-semibold text-white mb-2 font-en">Rad AI, at your fingertips.</h2>
      <p className="text-sm text-neutral-400 max-w-md mb-8">
        سوالات خود را درباره تولید، تجهیزات، نیروی انسانی و عملکرد عملیاتی معدن بپرسید.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-2xl">
        {EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => onPick(q)}
            className="text-right text-sm px-4 py-3 rounded-lg bg-neutral-900/60 border border-neutral-800 text-neutral-300 hover:border-[#E08A4F]/50 hover:bg-neutral-900 transition-colors"
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}