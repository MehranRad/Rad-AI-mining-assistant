'use client'

import React, { useRef, useCallback } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { cn } from '@/lib/utils'

type AICoreProps = {
  className?: string
}

export function AICore({ className }: AICoreProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)

  const springConfig = { stiffness: 120, damping: 20, mass: 0.5 }
  const rotateX = useSpring(useTransform(mouseY, [-0.5, 0.5], [12, -12]), springConfig)
  const rotateY = useSpring(useTransform(mouseX, [-0.5, 0.5], [-12, 12]), springConfig)
  const glowX = useSpring(useTransform(mouseX, [-0.5, 0.5], [-30, 30]), springConfig)
  const glowY = useSpring(useTransform(mouseY, [-0.5, 0.5], [-30, 30]), springConfig)

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const rect = containerRef.current?.getBoundingClientRect()
      if (!rect) return
      const x = (e.clientX - rect.left) / rect.width - 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5
      mouseX.set(x)
      mouseY.set(y)
    },
    [mouseX, mouseY]
  )

  const handleMouseLeave = useCallback(() => {
    mouseX.set(0)
    mouseY.set(0)
  }, [mouseX, mouseY])

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn('relative w-full h-full flex items-center justify-center', className)}
      style={{ perspective: 900 }}
    >
      <motion.div style={{ rotateX, rotateY }} className="relative w-60 h-60 md:w-80 md:h-80">
        <motion.div
          className="absolute -inset-3 rounded-full"
          style={{
            background:
              'conic-gradient(from 0deg, transparent, #F0A868 20%, transparent 42%, transparent 58%, #E08A4F 78%, transparent 100%)',
            filter: 'blur(1px)',
          }}
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 8, ease: 'linear' }}
        />

        <motion.div
          className="absolute inset-4 rounded-full border-2 border-[#F0A868]/80"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 14, ease: 'linear' }}
        />

        <motion.div
          className="absolute inset-8 rounded-full border border-[#F0A868]/40"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 5, ease: 'linear' }}
        />

        <div className="absolute inset-10 rounded-full bg-gradient-to-br from-neutral-400 via-neutral-700 to-neutral-900 border-2 border-[#F0A868] shadow-[0_0_130px_20px_rgba(240,168,104,0.6)] overflow-hidden">
          <motion.div
            className="absolute w-32 h-32 rounded-full blur-2xl"
            style={{
              background: 'radial-gradient(circle, rgba(240,168,104,1) 0%, rgba(240,168,104,0) 70%)',
              left: '50%',
              top: '50%',
              x: glowX,
              y: glowY,
              translateX: '-50%',
              translateY: '-50%',
            }}
          />
          <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: 'radial-gradient(circle at center, rgba(255,255,255,0.25), transparent 60%)' }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          />
          <div className="absolute top-7 left-9 w-12 h-12 rounded-full blur-md" style={{ background: 'rgba(255,255,255,0.45)' }} />
        </div>
      </motion.div>
    </div>
  )
}