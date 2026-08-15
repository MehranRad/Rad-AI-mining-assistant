'use client'

import { AICore } from "@/components/ui/ai-core"
import { Card } from "@/components/ui/card"
import { Spotlight } from "@/components/ui/spotlight"
import { ShiningText } from "@/components/ui/shining-text"

export function SplineSceneBasic() {
  return (
    <div className="p-10 space-y-10">
      <ShiningText text="Rad AI is thinking..." />
      <Card className="w-full h-[500px] bg-black/[0.96] relative overflow-hidden">
        <Spotlight className="-top-40 left-0 md:left-60 md:-top-20" fill="white" />
        <div className="flex h-full">
          <div className="flex-1 p-8 relative z-10 flex flex-col justify-center">
            <h1 className="text-4xl md:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-b from-neutral-50 to-neutral-400">
              Rad AI
            </h1>
            <p className="mt-4 text-neutral-300 max-w-lg">
              AI-powered intelligence for smarter mining operations.
            </p>
          </div>
          <div className="flex-1 relative">
            <AICore />
          </div>
        </div>
      </Card>
    </div>
  )
}