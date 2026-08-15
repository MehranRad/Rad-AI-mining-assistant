'use client'

import { Canvas, useFrame } from '@react-three/fiber'
import { MeshDistortMaterial, Float, Environment } from '@react-three/drei'
import { useRef } from 'react'
import * as THREE from 'three'

function CrystalMesh() {
  const groupRef = useRef<THREE.Group>(null)

  useFrame((state, delta) => {
    if (!groupRef.current) return
    groupRef.current.rotation.y += delta * 0.18

    // Subtle mouse-follow tilt
    const targetX = state.pointer.y * 0.35
    const targetZ = state.pointer.x * -0.2
    groupRef.current.rotation.x = THREE.MathUtils.lerp(
      groupRef.current.rotation.x,
      targetX,
      0.04
    )
    groupRef.current.rotation.z = THREE.MathUtils.lerp(
      groupRef.current.rotation.z,
      targetZ,
      0.04
    )
  })

  return (
    <Float speed={1.4} rotationIntensity={0.3} floatIntensity={0.7}>
      <group ref={groupRef}>
        <mesh>
          <icosahedronGeometry args={[1.5, 1]} />
          <MeshDistortMaterial
            color="#E08A4F"
            metalness={0.9}
            roughness={0.18}
            distort={0.22}
            speed={1.3}
            emissive="#8B4A28"
            emissiveIntensity={0.25}
          />
        </mesh>
        {/* Inner glowing core */}
        <mesh scale={0.5}>
          <icosahedronGeometry args={[1, 0]} />
          <meshBasicMaterial color="#F0A868" transparent opacity={0.5} />
        </mesh>
      </group>
    </Float>
  )
}

export function CopperCrystal({ className }: { className?: string }) {
  return (
    <div className={className} style={{ width: '100%', height: '100%' }}>
      <Canvas camera={{ position: [0, 0, 5], fov: 42 }} dpr={[1, 2]}>
        <ambientLight intensity={0.5} />
        <pointLight position={[5, 4, 5]} intensity={1.4} color="#E08A4F" />
        <pointLight position={[-5, -3, -4]} intensity={0.6} color="#5B8FD9" />
        <CrystalMesh />
        <Environment preset="city" />
      </Canvas>
    </div>
  )
}