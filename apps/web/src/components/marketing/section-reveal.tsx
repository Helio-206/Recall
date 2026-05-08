"use client";

import type { ComponentPropsWithoutRef, ReactNode } from "react";

import { motion, useReducedMotion } from "framer-motion";

import { cn } from "@/lib/utils";

type SectionRevealProps = ComponentPropsWithoutRef<typeof motion.div> & {
  children: ReactNode;
  delay?: number;
};

export function SectionReveal({ children, className, delay = 0, ...props }: SectionRevealProps) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <motion.div
      className={cn(className)}
      initial={prefersReducedMotion ? false : { opacity: 0, y: 28, filter: "blur(10px)" }}
      whileInView={prefersReducedMotion ? undefined : { opacity: 1, y: 0, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-80px" }}
      transition={prefersReducedMotion ? undefined : { duration: 0.7, ease: [0.22, 1, 0.36, 1], delay }}
      {...props}
    >
      {children}
    </motion.div>
  );
}