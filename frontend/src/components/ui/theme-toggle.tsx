"use client"

import * as React from "react"
import { Sun } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useTheme } from "@/lib/theme-provider"

export function ThemeToggle() {
  const { theme } = useTheme()

  return (
    <Button variant="outline" size="icon" disabled>
      <Sun className="h-[1.2rem] w-[1.2rem]" />
      <span className="sr-only">Light theme (enforced)</span>
    </Button>
  )
} 