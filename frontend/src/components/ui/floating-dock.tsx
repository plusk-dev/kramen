"use client";

import { cn } from "@/lib/utils";
import { useState } from "react";
import { Button } from "./button";
import { motion, AnimatePresence } from "motion/react";

export interface FloatingDockItem {
  title: string;
  icon: React.ReactNode;
  href?: string;
  onClick?: () => void;
}

interface FloatingDockProps {
  items: FloatingDockItem[];
  className?: string;
  mobileClassName?: string;
  onHoverChange?: (isHovered: boolean) => void;
}

export function FloatingDock({
  items,
  className,
  mobileClassName,
  onHoverChange,
}: FloatingDockProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [isDockHovered, setIsDockHovered] = useState(false);

  // Separate the plus button from other items
  const plusButton = items.find(item => item.title === "Add an Integration");
  const otherItems = items.filter(item => item.title !== "Add an Integration");
  
  // Show only first 4 items in main row when not hovered (plus the plus button)
  const visibleItems = isDockHovered 
    ? items // Show all items when hovered
    : (plusButton ? [plusButton, ...otherItems.slice(0, 4)] : otherItems.slice(0, 4)); // Show only 4 + plus when not hovered

  const handleMouseEnter = () => {
    setIsDockHovered(true);
    onHoverChange?.(true);
  };

  const handleMouseLeave = () => {
    setIsDockHovered(false);
    onHoverChange?.(false);
  };

  return (
    <div
      className={cn(
        "relative",
        className
      )}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* Main dock row - expands to show all items when hovered */}
      <motion.div 
        className="flex items-center justify-center"
        layout
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 30,
        }}
      >
        <AnimatePresence mode="popLayout">
          {visibleItems.map((item, index) => (
            <motion.div 
              key={`${item.title}-${index}`} 
              className="relative"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
              }}
              layout
            >
              <Button
                variant="ghost"
                size="sm"
                className={cn(
                  "h-16 w-16 p-0 rounded-full transition-all duration-200",
                  "hover:bg-muted-foreground/10 hover:scale-110",
                  hoveredIndex === index && "scale-110"
                )}
                onMouseEnter={() => setHoveredIndex(index)}
                onMouseLeave={() => setHoveredIndex(null)}
                onClick={item.onClick}
              >
                <div className="h-10 w-10">
                  {item.icon}
                </div>
              </Button>
              
              {/* Animated Tooltip */}
              <AnimatePresence>
                {hoveredIndex === index && (
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.8 }}
                    animate={{ 
                      opacity: 1, 
                      y: 0, 
                      scale: 1,
                      transition: {
                        type: "spring",
                        stiffness: 260,
                        damping: 20,
                      }
                    }}
                    exit={{ opacity: 0, y: 10, scale: 0.8 }}
                    className="absolute -top-14 left-1/2 transform -translate-x-1/2 z-50"
                  >
                    <div className="bg-background/95 backdrop-blur-sm border border-border rounded-lg px-3 py-2 shadow-lg">
                      <div className="text-sm font-medium text-foreground whitespace-nowrap">
                        {item.title}
                      </div>
                      {/* Tooltip arrow */}
                      <div className="absolute top-full left-1/2 transform -translate-x-1/2">
                        <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-border"></div>
                        <div className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-background/95 -mt-px"></div>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>
    </div>
  );
} 