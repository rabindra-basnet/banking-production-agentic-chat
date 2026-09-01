import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
        secondary: 'border-slate-800 bg-slate-900 text-slate-300',
        destructive: 'border-red-500/40 bg-red-500/10 text-red-400',
        outline: 'text-slate-300 border-slate-700',
        premium: 'border-amber-500/40 bg-amber-500/20 text-amber-300',
        privileged: 'border-purple-500/40 bg-purple-500/20 text-purple-300',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };
