"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight, Play } from "lucide-react";
import { AnimatedTooltip } from "@/components/animated-tooltip";

export function Hero() {
  const people = [
    {
      id: 1,
      name: "Stripe Integration",
      designation:
        "Talk about disputes, create subscriptions, etc. using just prompts!",
      image:
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT44LWV1mbueAGMd2V-BVH9tl81d_6gKEfMmg&s",
    },
    {
      id: 2,
      name: "Resend Integration",
      designation: "Send emails using just prompts!",
      image:
        "https://mintlify.s3-us-west-1.amazonaws.com/resend/_generated/favicon/apple-touch-icon.png?v=3",
    },
    {
      id: 3,
      name: "Linear Integration",
      designation:
        "Talk about issues, create tickets, etc. using just prompts!",
      image:
        "https://cdn.prod.website-files.com/5f15081919fdf673994ab5fd/6417e9db62883903b13efe0b_Linear%20Logo.svg",
    },
    {
      id: 4,
      name: "Cal.com Integration",
      designation: "Schedule meetings and manage bookings using just prompts!",
      image: "https://spp.co/assets/cal-com-logo.png",
    },
    {
      id: 5,
      name: "+100 More",
      designation: "And many more integrations coming soon!",
      image: "+100 More",
    },
  ];

  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <section
      className="relative flex flex-col items-center min-h-screen mt-3 mx-3 rounded-3xl overflow-hidden"
      style={{
        backgroundImage: 'url(https://img.freepik.com/premium-vector/add-modern-touch-with-our-captivating-gradient-wave-designs_884160-2479.jpg?semt=ais_hybrid&w=740)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/20 z-0 rounded-3xl pointer-events-none" />
      {/* Responsive, sticky, glass-effect Navbar inside Hero */}
      <div className="w-full flex justify-center px-6 sm:px-0 mt-6 sticky top-6 z-20">
        <nav
          className="lg:mx-6 w-full flex items-center justify-between px-4 py-3 bg-white/20 backdrop-blur-md rounded-2xl border border-white/30 shadow-lg relative"
        >
          <div className="lg:text-2xl text-xl text-white tracking-widest">kramen</div>
          <div className="hidden sm:flex gap-4">
            <a href="#" className="text-white/80 hover:text-white transition">Home</a>
            <a href="#" className="text-white/80 hover:text-white transition">Features</a>
            <a href="#" className="text-white/80 hover:text-white transition">Contact</a>
          </div>
          {/* Desktop Login button */}
          <div className="hidden sm:block ml-4">
            <Button variant="secondary" className="rounded-xl shadow-xl shadow-primary cursor-pointer">
              Login
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          {/* Mobile menu icon and Login button */}
          <div className="flex items-center gap-2 sm:hidden">
            <button
              className="text-white/80 hover:text-white focus:outline-none"
              aria-label="Open menu"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" /></svg>
            </button>
            <Button variant="secondary" className="rounded-xl shadow-xl shadow-primary cursor-pointer">
              Login
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          {/* Mobile dropdown menu */}
          {menuOpen && (
            <div className="absolute top-full left-0 w-full bg-white/80 backdrop-blur-lg rounded-b-2xl shadow-lg flex flex-col items-center py-2 sm:hidden animate-fade-in z-30">
              <a href="#" className="block w-full text-center py-2 text-primary hover:bg-primary/10 transition">Home</a>
              <a href="#" className="block w-full text-center py-2 text-primary hover:bg-primary/10 transition">Features</a>
              <a href="#" className="block w-full text-center py-2 text-primary hover:bg-primary/10 transition">Contact</a>
            </div>
          )}
        </nav>
      </div>
      {/* Text content container */}
      <div className="text-center relative z-10">
        <div className="p-8 sm:p-12">
          {/* Main heading */}
          <h1 className="text-3xl sm:text-4xl font-semibold tracking-wider lg:text-5xl text-white mb-6 leading-tight">
            your most productive intern
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-lg text-gray-200 mb-8 max-w-2xl leading-relaxed mx-auto">
            Humans were meant to think, not do ops. <br /> Let Kramen do the ops
            while you do the thinking.
          </p>

          {/* Animated Tooltip */}
          {/* removed AnimatedTooltip and its container */}

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-center">
            <Button
              // size="lg"
              className="text-xl p-6 cursor-pointer"
              variant={"secondary"}
            >
              Get Started Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}
