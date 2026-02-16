import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary-500/15 text-primary-400",
        secondary:
          "border-transparent dark:bg-dark-700 dark:text-dark-300 light:bg-light-200 light:text-light-600",
        destructive:
          "border-transparent bg-danger-500/15 text-danger-400",
        success:
          "border-transparent bg-success-500/15 text-success-400",
        warning:
          "border-transparent bg-warning-500/15 text-warning-500",
        outline: "dark:text-dark-300 dark:border-dark-600 light:text-light-600 light:border-light-400",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
