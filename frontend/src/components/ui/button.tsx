import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500/50 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default: "bg-primary-500 text-white shadow-sm hover:bg-primary-600 shadow-primary-500/25",
        destructive: "bg-danger-500 text-white shadow-sm hover:bg-danger-600 shadow-danger-500/25",
        outline: "border bg-transparent hover:text-dark-100 dark:hover:bg-dark-700/50 dark:border-dark-600 light:border-light-400 light:text-light-700 light:hover:bg-light-200",
        secondary: "shadow-sm hover:bg-dark-600 dark:bg-dark-700 dark:text-dark-100 light:bg-light-200 light:text-light-800 light:hover:bg-light-300",
        ghost: "hover:text-dark-100 dark:hover:bg-dark-700/50 light:text-light-600 light:hover:text-light-900 light:hover:bg-light-200",
        link: "text-primary-400 underline-offset-4 hover:underline",
        success: "bg-success-500 text-white shadow-sm hover:bg-success-600 shadow-success-500/25",
        warning: "bg-warning-500 text-dark-900 shadow-sm hover:bg-warning-600 shadow-warning-500/25",
      },
      size: {
        default: "h-9 px-4 py-2",
        sm: "h-8 rounded-md px-3 text-xs",
        lg: "h-10 rounded-lg px-8",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
